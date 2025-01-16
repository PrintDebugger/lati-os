import random
import discord
from discord.ext import commands
from cogs.moneygame import EmbedProfile, UserData
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
                await ctx.respond("You need to be Level {0} to use this command.".format(level))
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
            await ctx.respond("Viewing {0}'s profile".format(target.name), embed=EmbedProfile(target, user))
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

        if chance < 0.3:        # 30% chance
            earnings = random.randint(60,300)
            message = "You got ${0:,}, cool. Better than nothing."
        elif chance < 0.4:      # 10% chance
            earnings = random.randint(600,850)
            message = "Damn, you got ${0:,}? May be your lucky day."
        elif chance < 0.442:    # 4.2% chance
            earnings = random.randint(1200,1800)
            message = "${0:,}?? Holy COW, that's a lot of money!"
        elif chance < 0.45:     # 0.8% chance
            earnings = random.randint(3000,6000)
            message = "**WTF YOU GOT ${0:,}, HOW THE HELL???????**"
        else:
            earnings = 0
            message = "Lmao, you got ignored. You got ${0}"

        user = UserData(ctx.user)
        earnings = int(earnings * user.cash_multi)
        user.update('wallet', user.wallet + earnings)
        await ctx.respond(story + "\n" + message.format(earnings))
        await user.add_exp(10, ctx)

    @discord.slash_command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @registered_only()
    @level_limit(3)
    async def steal(self, ctx, target: discord.Member):
        """Steal someone's money."""
        if target.id == ctx.user.id:
            await ctx.respond("stealing from yourself? you ok ah bro")
        elif target.bot:
            await ctx.respond("You cannot steal from the bot because it is in the 4th dimension")
        else:
            victim = UserData(target)
            if victim.has_account:
                if victim.wallet < 200:
                    await ctx.respond("bro doesn't even have $200 leave him alone ba")
                elif victim.level < 3:
                    await ctx.respond("You cannot steal from someone who isn't Level 3 yet.")
                else:
                    chance = random.random()

                    if chance < 0.2:
                        stolen_money = round(victim.wallet * random.uniform(0.1, 0.3))
                        await ctx.respond("You stole ${0:,}, careful jangan ditangkap".format(stolen_money))
                    elif chance < 0.24:
                        stolen_money = round(victim.wallet * random.uniform(0.5, 0.9))
                        await ctx.respond("You stole a lot of money leh, you got ${0:,}, happy ma?".format(stolen_money))  
                    elif chance < 0.25:
                        stolen_money = victim.wallet
                        await ctx.respond("You stole FUCKING EVERYTHING (${0:,}), Gai Loooooooo".format(stolen_money))
                    else:
                        stolen_money = round(victim.wallet * random.uniform(0.01, 0.04))
                        await ctx.respond("You stole a small portion of their money... you got ${0:,}".format(stolen_money))

                    stealer = UserData(ctx.user)
                    stealer.update('wallet', stealer.wallet + stolen_money)
                    victim.update('wallet', victim.wallet - stolen_money)
            else:
                await ctx.respond("That person does not have an account.")

    @discord.slash_command()
    @registered_only()
    @discord.option('amount', int, min_value=1)
    async def give(self, ctx, amount: int, target: discord.Member):
        """Give your money to someone else."""
        if target.id == ctx.user.id:
            await ctx.respond("You cannot give money to yourself la bodoh...")
        else:
            donor = UserData(ctx.user)
            if donor.wallet == 0:
                await ctx.respond("You don't have any money to share.")
            elif amount > donor.wallet:
                await ctx.respond("You cannot share more than what you have (${0:,})".format(donor.wallet))
            else:
                receiver = UserData(target)
                if receiver.has_account:
                    result = await send_confirmation(ctx, ctx.user, 
                        "Are you sure you want to give ${0:,} to {1}?\n\n${2:,}  ►►►  ${3:,}".format(
                            amount, receiver.name, donor.wallet, donor.wallet - amount
                        )
                    )
                    if result:
                        donor.update('wallet', donor.wallet - amount)
                        receiver.update('wallet', receiver.wallet + amount)
                        await ctx.followup.send("{0} has gave {1} ${2:,}!".format(donor.name, receiver.name, amount))
                else:
                    await ctx.respond("That person does not have an account.")

    bank = discord.SlashCommandGroup("bank", "Bank operations")

    @bank.command()
    @registered_only()
    @level_limit(3)
    @discord.option('amount', int, min_value=1)
    async def deposit(self, ctx, amount: int):
        """Deposit some money into the bank."""
        user = UserData(ctx.user)
        if amount > user.wallet:
            await ctx.respond("Your wallet has only ${0:,}".format(user.wallet))
        else:
            user.update('wallet', user.wallet - amount)
            user.update('bank', user.bank + amount)
            await ctx.respond("Deposited ${0:,}, your bank now has ${1:,}".format(amount, user.bank))

    @bank.command()
    @registered_only()
    @level_limit(3)
    @discord.option('amount', int, min_value=1)
    async def withdraw(self, ctx, amount: int):
        """Withdraw some money from the bank."""
        user = UserData(ctx.user)
        if amount > user.bank:
            await ctx.respond("Your bank has only ${0:,}".format(user.bank))
        else:
            user.update('bank', user.bank - amount)
            user.update('wallet', user.wallet + amount)
            await ctx.respond("Withdrawn ${0:,}, your bank now has ${1:,}".format(amount, user.bank))

def setup(bot): # Pycord calls this function to setup this cog
    bot.add_cog(MoneyGame(bot))