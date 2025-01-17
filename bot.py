import os
import time
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

    async def on_application_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.respond(embed=discord.Embed(
                color = discord.Colour.brand_red(), 
                description = "You can use this command again in **{0:,} seconds**".format(round(error.retry_after))
            ))

    @commands.command()
    async def ping(ctx):
        """Shows my latency."""
        start_time = time.perf_counter()
        msg = await ctx.respond("Pong!")
        response = (time.perf_counter() - start_time) * 1000

        start_time = time.perf_counter()
        await msg.edit(content="Pong!\nInitial response: {0:.2f}ms".format(response))
        latency = (time.perf_counter() - start_time) * 1000

        await msg.edit(content="Pong!\nInitial response: {0:.2f}ms\nRound-trip latency: {1:.2f}ms".format(response, latency))