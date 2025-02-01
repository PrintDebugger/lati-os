import random
import discord
from discord.ext import commands

from cogs.moneygame import MoneyUser, MoneyItem, LuckHandler, ShopEmbed, Shop
from cogs.moneygame.constants import *
from cogs.moneygame.templates import EmbedProfile, Inventory, ItemInfo, BankBalance
from interactions import ConfirmAction, ConfirmEmbed
from utils import initialise_db, logger


class MoneyGame(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_before_invoke(self, ctx): # Add user data if they don't have any
        user = MoneyUser(ctx.user.id)

        if not user.has_account:
            user.create_account()


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
        async def predicate(ctx):
            user = MoneyUser(ctx.user.id)
            if user.level < level:
                await ctx.respond(f"You need to be Level {level} to use this command.")
                return False
            else:
                return True
        return discord.ext.commands.check(predicate)


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
        await ctx.respond(f"Viewing {target.name}'s profile", embed=EmbedProfile(target.display_name, target.avatar.url, user))


    @discord.slash_command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def beg(self, ctx):
        """Beg for a small amount money."""
        message = "> " + random.choice([
            "Someone walks past and notices you...",
            "You waited and waited... oh, someone's coming.",
            "You heard something... probably just the wind?",
            "You decided to breakdance and people thought you were a street performer... or a dumbass.",
            "You slept at the streets for the night."
        ]) + "\n"

        chance = random.random()
        outcome = LuckHandler.get_outcome('beg', chance)
        user = MoneyUser(ctx.user.id)
        ctx.level_data = await user.add_exp(10)

        if not outcome.success:
            message += "* Lmao you got ignored. You got 0 coins"
            return await ctx.respond(embed=discord.Embed(description=message, color=discord.Colour.brand_red()))

        base_earnings = random.randint(*outcome.info['coinRange'])
        earnings = int(base_earnings * user.calculate_cash_multi())
        message += f"* You got {earnings:,} coins!"
        await user.add_wallet(earnings)

        if 'items' in outcome.info:
            for item_id, x in outcome.info['items'].items():
                if random.random() < x:
                    get_item = MoneyItem.from_id(int(item_id))
                    await user.add_item(int(item_id), 1)
                    message += f"\n* You also got 1 {get_item.emoji} **{get_item.name}**!"
                    break

        await ctx.respond(embed=discord.Embed(description=message, color=discord.Colour.brand_green()))


    @discord.slash_command()
    @commands.cooldown(1, 20, commands.BucketType.user)
    @level_limit(ROB_MIN_LEVEL)
    async def steal(self, ctx, target: discord.Member):
        """Steal someone's money."""
        if target.id == ctx.user.id:
            return await ctx.respond("stealing from yourself? you ok ah bro")
        
        if target.bot:
            return await ctx.respond("You cannot steal from the bot because it is in the 4th dimension")
        
        stealer = MoneyUser(ctx.user.id)
        if stealer.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"You need at least ${ROB_MIN_AMOUNT} to steal, or else you end up in jail")

        victim = MoneyUser(target.id)
        if victim.level < ROB_MIN_LEVEL:
            return await ctx.respond(f"You cannot steal from someone who isn't Level {ROB_MIN_LEVEL} yet.")
        
        if victim.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"bro doesn't even have ${ROB_MIN_AMOUNT} leave him alone ba")
        
        chance = random.random()
        outcome = LuckHandler.get_outcome('steal', chance)
        if outcome.success:
            portion = random.uniform(*outcome.info['amountRange'])
            stolen = max(1, round(victim.wallet * portion))
            message = outcome.info['message'].format(stolen)
            color = discord.Colour.brand_green()
        else:
            stolen = - max(200, round(stealer.wallet * 0.05))
            message = (
                "Oof, you kena tangkap lol.\n"
                f"You paid {target.display_name} {abs(stolen):,} coins for trying to rob them."
            )
            color = discord.Colour.brand_red()
        
        await stealer.add_wallet(stolen)
        await victim.add_wallet(- stolen)
        ctx.level_data = await stealer.add_exp(10)
        await ctx.respond(embed=discord.Embed(description=message, color=color))


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
        
        await ctx.respond(f"{ctx.user.display_name} has gave {target.display_name} {amount:,} coins!")
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
        view = Shop(ctx.user, user)
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
            amount = MoneyUser(ctx.user.id).items.get(str(item.id), 0)
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
        user = MoneyUser(ctx.user.id)
        item = MoneyItem.from_name(name)
        item_id = item.id
        user_has_amount = user.items.get(str(item_id), 0)

        if amount > user_has_amount:
            return await ctx.respond(embed=discord.Embed(
                description = f"You only have {user_has_amount} {item.emoji} **{item.name}**"
            ))
        
        #   oh god
        if item_id == 1:
            embed = discord.Embed(
                color=None,
                title="IT'S RAINING COINS",
                description=f"{ctx.user.display_name} has fired a Gold Firework!\nClick the button to collect them!"
            )
            # send message


def setup(bot): # Pycord calls this function to setup this cog
    initialise_db()
    bot.add_cog(MoneyGame(bot))