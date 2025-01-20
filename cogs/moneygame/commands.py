import random
import discord
from discord.ext import commands
from cogs.moneygame import EmbedProfile, UserData
from cogs.moneygame.constants import *
from interactions import send_confirmation

class MoneyGame(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Money command check
    def registered_only():
        async def predicate(ctx):
            user = UserData(ctx.user)
            if user.has_account:
                return True
            else:
                await ctx.respond("You don't have an account. Run `/start` to create one!")
                return False
        return discord.ext.commands.check(predicate)

    def level_limit(level: int):
        async def predicate(ctx):
            user = UserData(ctx.user)
            if user.level < level:
                await ctx.respond(f"You need to be Level {level} to use this command.")
                return False
            else:
                return True
        return discord.ext.commands.check(predicate)
    
    @discord.slash_command()
    async def start(self, ctx):
        """Begin your journey in Money Game."""
        user = UserData(ctx.user)
        if user.has_account:
            await ctx.respond("You already created your account.")
        else:
            user.create_account()
            await ctx.respond("Welcome to Money Game! Here's 10,000 free dollars")

    @discord.slash_command()
    async def profile(self, ctx, target: discord.Member=None):
        """View someone's stats."""
        if not target:
            target = ctx.user

        user = UserData(target)

        if user.has_account:
            await ctx.respond(f"Viewing {target.name}'s profile", embed=EmbedProfile(target, user))
        else:
            if not target or target.id == ctx.user.id:
                await ctx.respond("You don't have an account. Run `/start` to create one!")
            else:
                await ctx.respond("That person hasn't created an account yet.")

    @discord.slash_command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @registered_only()
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

        user = UserData(ctx.user)
        earnings = int(earnings * user.cash_multi)
        await ctx.respond(story + "\n" + message.format(earnings))
        await user.add_exp(10, ctx)

        if earnings != 0:
            await user.update('wallet', user.wallet + earnings)

    @discord.slash_command()
    @commands.cooldown(1, 20, commands.BucketType.user)
    @registered_only()
    @level_limit(ROB_MIN_LEVEL)
    async def steal(self, ctx, target: discord.Member):
        """Steal someone's money."""
        if target.id == ctx.user.id:
            return await ctx.respond("stealing from yourself? you ok ah bro")
        
        if target.bot:
            return await ctx.respond("You cannot steal from the bot because it is in the 4th dimension")
        
        stealer = UserData(ctx.user)
        victim = UserData(target)

        if stealer.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"You need at least ${ROB_MIN_AMOUNT} to steal, or else you end up in jail")
        
        if not victim.has_account:
            return await ctx.respond("That person does not have an account.")

        if victim.level < ROB_MIN_LEVEL:
            return await ctx.respond(f"You cannot steal from someone who isn't Level {ROB_MIN_LEVEL} yet.")
        
        if victim.wallet < ROB_MIN_AMOUNT:
            return await ctx.respond(f"bro doesn't even have ${ROB_MIN_AMOUNT} leave him alone ba")
        
        chance = random.random()
        success = True

        if chance > 0.99:
            stolen_money = victim.wallet
            message = "🤑 WTF YOU STOLE **EVERYTHING** (${0:,}), Gai Loooooo"
        elif chance > 0.93:
            stolen_money = round(victim.wallet * 0.7)
            message = "💰 You stole a lot of money leh, you got ${0:,}, happy ma?" 
        elif chance > 0.6:
            stolen_money = round(victim.wallet * 0.3)
            message = "💸 You stole some money and quietly left... you got ${0:,}."
        else:
            success = False
            stolen_money = -1 * max([200, round(stealer.wallet * 0.05)])

        if success:    
            await ctx.respond(message.format(stolen_money))
        else:
            await ctx.respond(f"Oof, you kena tangkap lol. You paid {victim.name} ${(-1 * stolen_money):,} for trying to rob them.")

        await stealer.update('wallet', stealer.wallet + stolen_money)
        await victim.update('wallet', victim.wallet - stolen_money)            

    @discord.slash_command()
    @registered_only()
    @discord.option('amount', int, min_value=1)
    async def give(self, ctx, amount: int, target: discord.Member):
        """Give your money to someone else."""
        if target.id == ctx.user.id:
            await ctx.respond("You cannot give money to yourself la bodoh")
        else:
            donor = UserData(ctx.user)
            if donor.wallet == 0:
                await ctx.respond("You don't have any money to share.")
            elif amount > donor.wallet:
                await ctx.respond(f"You cannot share more than what you have (${donor.wallet:,})")
            else:
                receiver = UserData(target)
                if receiver.has_account:
                    result = await send_confirmation(ctx, ctx.user, 
                        "Are you sure you want to give ${0:,} to {1}?\n\n${2:,}  ►►►  ${3:,}".format(
                            amount, receiver.name, donor.wallet, donor.wallet - amount
                        )
                    )
                    if result:
                        await ctx.followup.send(f"{donor.name} has gave {receiver.name} ${amount:,}!")
                        await donor.update('wallet', donor.wallet - amount)
                        await receiver.update('wallet', receiver.wallet + amount)
                else:
                    await ctx.respond("That person does not have an account.")

    bank = discord.SlashCommandGroup("bank", "Bank operations")

    @bank.command()
    @registered_only()
    @level_limit(BANK_MIN_LEVEL)
    @discord.option('amount', int, min_value=1)
    async def deposit(self, ctx, amount: int):
        """Deposit some money into the bank."""
        user = UserData(ctx.user)
        if amount > user.wallet:
            await ctx.respond(f"Your wallet has only ${user.wallet:,}")
        else:
            await user.update('wallet', user.wallet - amount)
            await user.update('bank', user.bank + amount)
            await ctx.respond(f"Deposited ${amount:,}, your bank now has ${user.bank:,}")

    @bank.command()
    @registered_only()
    @level_limit(BANK_MIN_LEVEL)
    @discord.option('amount', int, min_value=1)
    async def withdraw(self, ctx, amount: int):
        """Withdraw some money from the bank."""
        user = UserData(ctx.user)
        if amount > user.bank:
            await ctx.respond(f"Your bank has only ${user.bank:,}")
        else:
            await user.update('bank', user.bank - amount)
            await user.update('wallet', user.wallet + amount)
            await ctx.respond(f"Withdrawn ${amount:,}, your bank now has ${user.bank:,}")

def setup(bot): #   Pycord calls this function to setup this cog
    bot.add_cog(MoneyGame(bot))