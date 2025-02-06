import time
import discord
from discord.ext import commands

from cogs.misc.gacha import Delivery
from cogs.misc.illust import ImageCommand
from utils import logger

class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @discord.slash_command()
    async def ping(self, ctx):
        """Shows my latency."""
        msg = await ctx.respond("Pong!")
        response = self.bot.latency * 1000
        start_time = time.perf_counter()
        await msg.edit(content=f"Pong!\nInitial response: {response:.2f}ms")
        latency = (time.perf_counter() - start_time) * 1000
        await msg.edit(content=f"Pong!\nInitial response: {response:.2f}ms\nRound-trip latency: {latency:.2f}ms")


    @discord.slash_command()
    async def gacha(self, ctx):
        """A simulation of Pokemon Cafe Remix's delivery feature."""
        embed = discord.Embed(
            color = 0x00aafc,
            title = "Delivery Simulator",
            description = "{0} It's time to hunt some pelicans.".format(ctx.user.mention),
        )
        view = Delivery(ctx.user, embed)
        await ctx.respond(embed=embed, view=view)


    @discord.slash_command()
    @discord.option("pokemon", str, autocomplete=discord.utils.basic_autocomplete(['latias', 'latios', 'meowscarada']))
    async def pokeart(self, ctx,  pokemon):
        '''Returns some pokemon art!'''
        try:
            data = ImageCommand.get_random_image(pokemon)
            embed = discord.Embed(color=0x759cf7, description=f"` Artist ` {data['artist']}")
            embed.set_image(url=data['url'])
            embed.set_footer(text=f"Tags: {', '.join(data['tags'])}")
        except Exception:
            embed = discord.Embed(color = 0xff61bb, description="Shoot, something went wrong.")
            logger.exception("Unable to load image")

        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Misc(bot))