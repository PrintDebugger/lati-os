import os
import time
import discord
from utils import initialise_db, log
from interactions import Delivery
from dotenv import load_dotenv
from bot import LatiBot

load_dotenv()
TOKEN = os.environ['BOT_TOKEN']


bot = discord.Bot(debug_guilds=[1214372737313931304])

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