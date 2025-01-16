import os
import discord
from discord.ext import commands
from utils import initialise_db, log
from interactions import Delivery
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ['BOT_TOKEN']


bot = discord.Bot(debug_guilds=[1214372737313931304])


@bot.event
async def on_ready():
    await bot.sync_commands()
    log("{0} has connected to Discord".format(bot.user))

@bot.event
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.respond(embed=discord.Embed(
            color = discord.Colour.brand_red(), 
            description = "You can use this command again in **{0:,} seconds**".format(round(error.retry_after))
        ))

#   Misc commands go here idk why
@bot.command()
async def ping(ctx):
    """Shows my latency."""
    await ctx.respond("Latency: {0:.2f}ms".format(bot.latency * 1000))

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
cogs = ['cogs.moneygame.commands']

for cog in cogs:
    bot.load_extension(cog)
    log("Loaded extension {0}".format(cog))


initialise_db()
bot.run(TOKEN)