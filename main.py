import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

from utils import log


load_dotenv()
TOKEN = os.environ['BOT_TOKEN']


class LatiBot(discord.Bot):

    def __init__(self, debug_guilds=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_guilds = debug_guilds or []

    async def on_ready(self):
        await self.sync_commands()
        log(f"{self.user} has connected to Discord")

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            return await ctx.respond(embed=discord.Embed(
                description = f"You can use this command again in **{round(error.retry_after):,} seconds**"
            ))
        
        if isinstance(error, discord.errors.CheckFailure):
            return

        await ctx.respond(embed=discord.Embed(
            title = "Uh oh...",
            description = f"An error occured while trying to run the `/{ctx.command}` command."
        ))
        log(f"❌ Command {ctx.command} raised an exception:\n{str(error)}")


#   Load cogs
cogs = [
    'cogs.misc.commands',
    'cogs.moneygame.commands',
    #'cogs.ai.commands'
]

bot = LatiBot(debug_guilds=[1214372737313931304])

for cog in cogs:
    try:
        bot.load_extension(cog)
        log(f"Loaded extension {cog}")
    except Exception as e:
        log(f"❌ ERROR: Failed to load extension {cog}")
        print(e)

bot.run(TOKEN)