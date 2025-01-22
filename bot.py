import discord
from discord.ext import commands
from utils import log


class LatiBot(discord.Bot):

    def __init__(self, debug_guilds=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_guilds = debug_guilds or []

    async def on_ready(self):
        await self.sync_commands()
        log("{0} has connected to Discord".format(self.user))

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.respond(embed=discord.Embed(
                description = "You can use this command again in **{0:,} seconds**".format(round(error.retry_after))
            ))
        else:
            await ctx.respond(embed=discord.Embed(
                title = "Uh oh...",
                description = f"An error occured while trying to run the `/{ctx.command}` command."
            ))
            print(f"❌ ERROR: in command '{ctx.command}'\n{error}")