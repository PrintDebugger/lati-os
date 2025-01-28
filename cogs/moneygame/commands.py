import discord
import random
from discord.ext import commands

from cogs.moneygame import MoneyUser, ShopEmbed, Shop
from cogs.moneygame.constants import *
from cogs.moneygame.templates import EmbedProfile, Inventory
from interactions import send_confirmation
from utils import initialise_db


class MoneyGame(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_before_invoke(self, ctx): # Some commands require an account i.e. a MoneyUser to be used
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
                f"You earned ${rewards:,}"
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
        story = random.choice([
            "Someone walks past and notices you...",
            "You waited and waited... oh, someone's coming.",
            "You heard something... probably just the wind?",
            "You decided to breakdance and people thought you were a street performer... or a dumbass.",
            "You slept at the streets for the night."
        ])

        chance = random.random()
        if chance < 0.4:        # 40% chance
            earnings = random.randint(60,300)
            message = "You got ${0:,}, cool. Better than nothing."
        elif chance < 0.54:     # 14% chance
            earnings = random.randint(600,850)
            message = "Damn, you got ${0:,}? May be your lucky day."
        elif chance < 0.592:    # 5.2% chance
            earnings = random.randint(1200,1800)
            message = "${0:,}?? Holy COW, that's a lot of money!"
        elif chance < 0.6:      # 0.8% chance
            earnings = random.randint(3000,6000)
            message = "**WTF YOU GOT ${0:,}, HOW THE HELL???????**"
        else:
            earnings = 0
            message = "Lmao, you got ignored. You got ${0}"

        user = MoneyUser(ctx.user.id)
        earnings = int(earnings * user.calculate_cash_multi())
        await ctx.respond(story + "\n" + message.format(earnings))
        ctx.level_data = await user.add_exp(10)

        if earnings != 0:
            await user.add_wallet(earnings)


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
        victim = MoneyUser(target.id)
        if stealer.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"You need at least ${ROB_MIN_AMOUNT} to steal, or else you end up in jail")

        if victim.level < ROB_MIN_LEVEL:
            return await ctx.respond(f"You cannot steal from someone who isn't Level {ROB_MIN_LEVEL} yet.")
        
        if victim.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"bro doesn't even have ${ROB_MIN_AMOUNT} leave him alone ba")
        
        chance = random.random()
        success = True
        if chance > 0.992:
            portion = 1
            message = "🤑 WTF YOU STOLE **EVERYTHING** (${0:,}), Gai Loooooo"
        elif chance > 0.95:
            portion = random.uniform(0.5, 0.75)
            message = "💰 You stole a lot of money leh, you got ${0:,}, happy ma?"
        elif chance > 0.6:
            portion = random.uniform(0, 0.35)
            message = "💸 You stole some money and quietly left... you got ${0:,}."
        else:
            success = False

        if success:
            stolen_money = max(1, round(victim.wallet * portion))
            await ctx.respond(message.format(stolen_money))
        else:
            stolen_money = - max(200, round(stealer.wallet * 0.05))
            await ctx.respond(f"Oof, you kena tangkap lol. You paid {target.display_name} ${abs(stolen_money):,} for trying to rob them.")
        
        await stealer.add_wallet(stolen_money)
        await victim.add_wallet(- stolen_money)
        ctx.level_data = await stealer.add_exp(10)


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
            return await ctx.respond(f"You cannot share more than what you have (${donor.wallet:,})")

        result = await send_confirmation( 
            "Are you sure you want to give ${0:,} to {1}?\n\n${2:,}  ►  ${3:,}".format(
                amount, target.name, donor.wallet, donor.wallet - amount
            ),
            user = ctx.user,
            ctx = ctx
        )
        if not result == True:
            return
        
        await ctx.respond(f"{ctx.user.display_name} has gave {target.display_name} ${amount:,}!")
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
            return await ctx.respond(f"Your wallet has only ${user.wallet:,}")

        await user.add_bank(amount)
        await ctx.respond(f"Deposited ${amount:,}, your bank now has ${user.bank:,}")
        ctx.level_data = await user.add_exp(10)


    @bank.command()
    @level_limit(BANK_MIN_LEVEL)
    @discord.option('amount', int, min_value=1)
    async def withdraw(self, ctx, amount):
        """Withdraw some money from the bank."""
        user = MoneyUser(ctx.user.id)
        if amount > user.bank:
            return await ctx.respond(f"Your bank has only ${user.bank:,}")

        await user.add_bank(- amount)
        await ctx.respond(f"Withdrawn ${amount:,}, your bank now has ${user.bank:,}")
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
        await ctx.respond(embed=ShopEmbed(user), view=Shop(ctx.user, user))
        

def setup(bot): # Pycord calls this function to setup this cog
    initialise_db()
    bot.add_cog(MoneyGame(bot))