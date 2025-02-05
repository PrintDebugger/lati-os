import discord
import time
from discord.ext import commands

from cogs.ai.sightengine import detect_ai
from utils import progress_bar, logger

class AI(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def detect_ai(self, ctx, image_file:discord.Attachment=None, image_url:str=None):
        """Checks if an image if generated by AI."""
        if image_file == image_url == None:
            await ctx.respond("You have to provide an image file or the image url.")
            return
        elif image_file != None:
            image_url = image_file.url

        message = await ctx.respond(embed=discord.Embed(description="Processing your request..."))
        start_time = time.perf_counter()
        response = await self.bot.loop.run_in_executor(None, detect_ai, image_url) #   Returns json file containing the response info.

        if not response or response['status'] == "failure":
            return await message.edit(embed=discord.Embed(
                color=discord.Colour.brand_red(),
                description="Request failed. Please try again later."
            ))

        duration = time.perf_counter() - start_time
        percentage = response['type']['ai_generated']

        if percentage > 0.7:
            result = "This image is very likely to be generated by AI."
        elif percentage > 0.4:
            result = "This image may be generated by AI."
        else:
            result = "This image is very unlikely to be generated by AI."

        bar = progress_bar(percentage, 10)
        await message.edit(embed=discord.Embed(
            title="Result",
            description="[[image source]]({0})\n\n{1} **{2}%**\n{3}\n\n-# Process took {4:.2f} seconds\n-# powered by **sightengine.com**".format(
                image_url, bar, round(percentage*100), result, duration
            )
        ))

def setup(bot): #   Pycord calls this function to setup this cog
    bot.add_cog(AI(bot))