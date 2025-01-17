import os
import time
import discord
from utils import initialise_db, log
from interactions import Delivery
from dotenv import load_dotenv
from bot import LatiBot

load_dotenv()
TOKEN = os.environ['BOT_TOKEN']


bot = LatiBot(debug_guilds=[1214372737313931304])


#    Misc commands

@bot.command()
async def ping(ctx):
    """Shows my latency."""
    start_time = time.perf_counter()
    msg = await ctx.respond("Pong!")
    response = (time.perf_counter() - start_time) * 1000

    start_time = time.perf_counter()
    await msg.edit(content="Pong!\nInitial response: {0:.2f}ms".format(response))
    latency = (time.perf_counter() - start_time) * 1000

    await msg.edit(content="Pong!\nInitial response: {0:.2f}ms\nRound-trip latency: {1:.2f}ms".format(response, latency))

@bot.command()
async def gacha(ctx):
    """A simulation of Pokemon Cafe Remix's delivery feature."""
    embed = discord.Embed(
        color = 0x00aafc,
        title = "Delivery Simulator",
        description = "{0} It's time to hunt some pelicans.".format(ctx.user.mention),
    )
    view = Delivery(ctx.user, embed)
    await ctx.respond(embed=embed, view=view)


#   Load cogs
cogs = [
    'cogs.moneygame.commands',
    'cogs.ai.commands'
]

for cog in cogs:
    bot.load_extension(cog)
    log("Loaded extension {0}".format(cog))


initialise_db()
bot.run(TOKEN)