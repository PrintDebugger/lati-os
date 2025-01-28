import os
import time
import discord
from dotenv import load_dotenv

from cogs.misc import Delivery
from utils import log
from bot import LatiBot

load_dotenv()
TOKEN = os.environ['BOT_TOKEN']


bot = LatiBot(debug_guilds=[1214372737313931304])


#    Misc commands

@bot.command()
async def ping(ctx):
    """Shows my latency."""
    msg = await ctx.respond("Pong!")
    response = bot.latency * 1000
    start_time = time.perf_counter()
    await msg.edit(content=f"Pong!\nInitial response: {response:.2f}ms")
    latency = (time.perf_counter() - start_time) * 1000
    await msg.edit(content=f"Pong!\nInitial response: {response:.2f}ms\nRound-trip latency: {latency:.2f}ms")

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
    try:
        bot.load_extension(cog)
        log(f"Loaded extension {cog}")
    except Exception as e:
        log(f"❌ ERROR: Failed to load extension {cog}")
        print(e)

bot.run(TOKEN)