import random
import time
import discord
from discord.ext import commands

from .classes import MoneyUser, MoneyItem, LuckHandler
from .config import *
from .functions import (
    BegCommand,
    StealCommand,
    ShopEmbed, ShopView
)
from .templates import (
    EmbedProfile, 
    Inventory, 
    ItemInfo, 
    BankBalance, 
    SingleItemMessage
)
from interactions import ConfirmAction, ConfirmEmbed
from utils import initialise_db, logger


class MoneyGame(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_before_invoke(self, ctx): # Add user data if they don't have any
        user = MoneyUser(ctx.user.id)

        if not user.has_account:
            return user.create_account()
        
        if not user.active_items:
            return
        
        #   Check for expired items
        item_list = ""
        current_time = time.time()
        for item_id, expire_time in user.active_items.items():
            if expire_time < current_time:
                item = MoneyItem.from_id(item_id)
                await user.deactivate_item(item_id)
                item_list += f"\n* {item.emoji} **{item.name}**"

        if not item_list:
            return
        
        await ctx.user.send(embed=discord.Embed(
            title = "Item Expired",
            description = "Uh oh! Some of your items have expired." + item_list,
            color = discord.Colour.brand_red()
        ))


    async def cog_after_invoke(self, ctx): # Send level up message after a command (if the user levels up)
        if not hasattr(ctx, 'level_data'):
            return
        
        if not ctx.level_data['hasLeveledUp']:
            return
        
        rewards = ctx.level_data['rewards']
        level = ctx.level_data['level']
        if rewards > 0:
            await ctx.respond(
                f"{ctx.user.mention} Great job on reaching level {level}!\n"
                f"You earned {rewards:,} coins."
            )
        else:
            await ctx.respond(f"{ctx.user.mention} You are now level {level}!")


    def level_limit(level: int): # Some commands require the user's level to be a certain amount 
        async def predicate(ctx) -> bool:
            user = MoneyUser(ctx.user.id)
            if user.level < level:
                await ctx.respond(f"You need to be Level {level} to use this command.")
                return False
            else:
                return True
        return discord.ext.commands.check(predicate)


    async def kill(self, user, message) -> discord.Message:
        if "3" in user.items: # user revived
            await user.add_item(3, -1)
            left = user.items.get("3", 0)
            wallet = None
        else:
            left = None
            wallet = user.wallet
            await user.add_wallet(-user.wallet)

        receiver = await self.bot.fetch_user(user.id) 
        item = MoneyItem.from_id(3)

        #   Send death message
        return await receiver.send(embed = discord.Embed(
            color = 0xff61bb,
            title = (
                "Reviver Seed used!"
                if left
                else "You died!"
            ),
            description = f"You died while {message}!" + (
                f" BUT your {item.emoji} **{item.name}** activated and prevented you from actually dying!\n"
                f"* You have {left} {item.emoji} **{item.name}** left."
                if left
                else f"\n* You lost **{wallet} coins**."
            )
        ))

    #   COMMANDS

    @discord.slash_command()
    async def profile(self, ctx, target: discord.Member=None):
        """View someone's stats."""
        if not target:
            target = ctx.user

        user = MoneyUser(target.id)
        if not user.has_account:
            user.create_account()
        
        user.load_all()
        await ctx.respond(f"Viewing {target.name}'s profile", embed=EmbedProfile(target.name, target.avatar.url, user))


    @discord.slash_command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def beg(self, ctx):
        """Beg for a small amount money."""
        try:
            message = f"> {BegCommand.get_random_message()}\n"
        except Exception:
            message = "> You tried begging on the streets\n"
            logger.exception("Unable to generate beg message")

        chance = random.random()
        outcome = LuckHandler.get_outcome('beg', chance)
        user = MoneyUser(ctx.user.id)

        if not outcome.success:
            message += "* Lmao you got ignored. You got 0 coins"
            await ctx.respond(embed=discord.Embed(description=message, color=0xff61bb))
        else:
            base_earnings = random.randint(*outcome.info['coinRange'])
            earnings = int(base_earnings * user.coin_multi)
            message += f"* You got {earnings:,} coins!"

            get_item = None
            if 'items' in outcome.info:
                for item_id, x in outcome.info['items'].items():
                    if random.random() < x:
                        get_item = MoneyItem.from_id(int(item_id))
                        message += f"\n* You also got 1 {get_item.emoji} **{get_item.name}**!"
                        break

            await ctx.respond(embed=discord.Embed(description=message, color=0x70d772))
            await user.add_wallet(earnings)
            if get_item:
                await user.add_item(get_item.id, 1)
                
        ctx.level_data = await user.add_exp(10)


    @discord.slash_command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @level_limit(ROB_MIN_LEVEL)
    async def steal(self, ctx, target: discord.Member):
        """Steal someone's money."""

        if target.id == ctx.user.id:
            return await ctx.respond("stealing from yourself? you ok ah bro")
        if target.bot:
            return await ctx.respond("You cannot steal from the bot because it is in the 4th dimension")
        
        stealer = MoneyUser(ctx.user.id)
        victim = MoneyUser(target.id)

        if stealer.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"You need at least {ROB_MIN_AMOUNT} coins to steal, or else you end up in jail")
        if victim.level < ROB_MIN_LEVEL:
            return await ctx.respond(f"You cannot steal from someone who isn't Level {ROB_MIN_LEVEL} yet.")
        if victim.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"bro doesn't even have {ROB_MIN_AMOUNT} coins leave him alone ba")

        result, outcome = StealCommand.get_steal_result(stealer, victim)

        if result != "OTHER":
            stolen_amount = round(
                -max(200, stealer.wallet * 0.05)
                if 'FAIL' in result
                else max(1, victim.wallet * random.uniform(*outcome['amountRange']))
            )
        else:
            stolen_amount = None

        msg, color = StealCommand.generate_response(result, outcome, target, stolen_amount)
        response = await ctx.respond(embed=discord.Embed(description=msg, color=color))
        steal_msg = await response.original_response()

        padlock_break = (result == "FAIL_PADLOCK") and (random.random() < 0.15) # 15% chance to break padlock

        if result != "OTHER":
            ctx.level_data = await stealer.add_exp(10)
            await stealer.add_wallet(stolen_amount)
            await victim.add_wallet(-stolen_amount)
            if padlock_break:
                await victim.deactivate_item(5)
        else:
            await victim.deactivate_item(6)
            await self.kill(stealer, "trying to steal some money")
        
        #   Send DM to the victim
        try:
            title, dm_msg = StealCommand.generate_dm(result, ctx.user.name, padlock_break, stolen_amount)      
            await target.send(embed = discord.Embed(title=title, description=(dm_msg+"\n\n"+ steal_msg.jump_url), color=0xff61bb))
        except Exception: 
            logger.exception("Failed to send DM")

    @discord.slash_command()
    @discord.option('amount', int, min_value=1)
    async def give(self, ctx, amount: int, target: discord.Member):
        """Give your money to someone else."""
        if target.id == ctx.user.id:
            return await ctx.respond("You cannot give money to yourself la bodoh")

        receiver = MoneyUser(target.id)
        if not receiver.has_account:
            receiver.create_account()
        
        donor = MoneyUser(ctx.user.id)
        if donor.wallet == 0:
            return await ctx.respond("You don't have any money to share.")
    
        if amount > donor.wallet:
            return await ctx.respond(f"You cannot share more than what you have ({donor.wallet:,} coins)")

        embed = ConfirmEmbed(
            f"Are you sure you want to give {amount:,} coins to {target.name}?",
            ("Current Balance", f"{COIN} `{donor.wallet:,}`", True),
            ("New Balance", f"{COIN} `{(donor.wallet - amount):,}`", True)
        )
        view = ConfirmAction(ctx.user, embed)
        view.message = await ctx.respond(ctx.user.mention, embed=embed, view=view)
        await view.wait()
        if not view.result:
            return
        
        await ctx.respond(f"{ctx.user.name} has gave {target.name} {amount:,} coins!")
        await donor.add_wallet(- amount)
        await receiver.add_wallet(amount)
        ctx.level_data = await donor.add_exp(10)


    bank = discord.SlashCommandGroup("bank", "Bank operations")

    @bank.command()
    @level_limit(BANK_MIN_LEVEL)
    @discord.option('amount', int, min_value=1)
    async def deposit(self, ctx, amount):
        """Deposit some money into the bank."""
        user = MoneyUser(ctx.user.id)
        if amount > user.wallet:
            return await ctx.respond(f"Your wallet has only {user.wallet:,} coins")
        
        if user.bank >= user.max_bank:
            return await ctx.respond(f"Your bank is full! Run commands to level up or use bank notes and try again.")
        
        if user.bank + amount > user.max_bank:
            amount = user.max_bank - user.bank

        await user.add_bank(amount)
        await ctx.respond(embed=BankBalance("Deposited", amount, user))
        ctx.level_data = await user.add_exp(10)


    @bank.command()
    @level_limit(BANK_MIN_LEVEL)
    @discord.option('amount', int, min_value=1)
    async def withdraw(self, ctx, amount):
        """Withdraw some money from the bank."""
        user = MoneyUser(ctx.user.id)
        if amount > user.bank:
            return await ctx.respond(f"Your bank has only {user.bank:,} coins")

        await user.add_bank(- amount)
        await ctx.respond(embed=BankBalance("Withdrew", amount, user))
        ctx.level_data = await user.add_exp(10)


    @discord.slash_command()
    async def inventory(self, ctx, target:discord.Member=None):
        '''Check someone's inventory.'''
        if target is None:
            target = ctx.user

        user = MoneyUser(target.id)
        if not user.has_account:
            user.create_account()

        items = user.items
        await ctx.respond(f"Viewing {target.name}'s inventory", embed=Inventory(items))


    @discord.slash_command()
    async def shop(self, ctx):
        '''Buy some items.'''
        user = MoneyUser(ctx.user.id)
        view = ShopView(ctx.user, user)
        view.message = await ctx.respond(embed=ShopEmbed(user), view=view)
    

    @discord.slash_command()
    @discord.option(
        "name", str,
        description = "The name of the item.", 
        autocomplete = MoneyItem.get_matching_items
    )
    async def item(self, ctx, name):
        '''View the details of an item.'''
        try:
            item = MoneyItem.from_name(name)
            amount = MoneyUser(ctx.user.id).items.get(item.id, 0)
        except Exception:
            logger.exception("Failed to fetch item info")

        await ctx.respond(embed=ItemInfo(item, amount))


    @discord.slash_command()
    @discord.option(
        "name", str,
        description = "The name of the item.", 
        autocomplete = MoneyItem.get_matching_items
    )
    @discord.option(
        'amount', int,
        description = "The amount you want to use.",
        min_value = 1,
        default = 1
    )
    async def use(self, ctx, name, amount):
        '''Use an item.'''
        item = MoneyItem.from_name(name)
        if item is None:
            return await ctx.respond("That item doesn't exist bro")
        item_id = item.id   # store as variable as this is checked frequently
        
        user = MoneyUser(ctx.user.id)
        user_has_amount = user.items.get(item_id, 0)
        if user_has_amount < amount:
            return await ctx.respond(embed=discord.Embed(
                description = f"You only have {user_has_amount} {item.emoji} **{item.name}**"
            ))
        
        effect_duration = 0 # Initialise effect duration for items that can be activated

        #   YandereDev if else shit goes here
        if item_id == '1': # gold firework
            amount = 1
            return await ctx.respond("You can't use this item yet. Please stand by!")
            '''
            embed = discord.Embed(
                color=0xff9988,
                title="IT'S RAINING COINS",
                description=f"{ctx.user.display_name} has fired a Gold Firework!\nClick the button to collect them!"
            )
            '''
            # send message

        elif item_id == '2': # banknote
            increase = 0
            for _ in range(amount):
                increase += random.randint(5000, 25000)
            embed = discord.Embed(description=f"{amount} {item.emoji} **Bank Note** used.")
            embed.add_field(name="Amount Added", value=f"{COIN} `{increase:,}`", inline=False)
            embed.add_field(name="Total Bank Space", value=f"{COIN} `{(user.max_bank + increase):,}`")
            await user.increase_max_bank(increase)

        elif item_id == '3': # reviver
            return await ctx.respond("You're still alive! Save this item for later, 'kay?")

        elif item_id == '4': # apple
            amount = 1
            effect_duration = 10800
            embed = SingleItemMessage("You are less likely to die for the next 3 hours.", item)

        elif item_id == '5': # padlock
            amount = 1
            effect_duration = 7 * 86400
            embed = SingleItemMessage("Your wallet is protected for 1 week.\n* Be careful though, your padlock may break if someone tries to steal from you.", item)

        elif item_id == '6': # bomb trap
            amount = 1
            effect_duration = 86400
            embed = SingleItemMessage("Anyone who tries to steal from you for the next 24 hours has a 50% chance to step on it and die.", item)

        elif item_id == '7': # feather
            return await ctx.respond("There's nothing useful about this feather. Consider selling it?")

        else:
            return await ctx.respond("You can't use this item yet. Please stand by!")
        
        await ctx.respond(embed=embed)
        if amount:
            await user.add_item(item_id, -amount)
        if effect_duration:
            await user.activate_item(item_id, effect_duration)


def setup(bot): # Pycord calls this function to setup this cog
    initialise_db()
    bot.add_cog(MoneyGame(bot))