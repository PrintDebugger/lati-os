import discord

class Confirm(discord.ui.View):
    def __init__(self, user:discord.Member, embed):
        super().__init__(timeout=30)
        self.user = user
        self.embed = embed
        self.result = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("This confirmation isn't for you!", ephemeral=True)
            return False
        else:
            return True
        
    async def on_timeout(self):
        self.disable_all_items()
        self.embed.title = "Timed Out"
        self.embed.colour = discord.Colour.brand_red()
        await self.message.edit(embed=self.embed, view=self)
        self.stop()
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button:discord.ui.Button, interaction:discord.Interaction):
        self.result = False
        self.disable_all_items()
        self.children[1].style = discord.ButtonStyle.gray
        self.embed.title = "Action Cancelled"
        self.embed.colour = discord.Colour.brand_red()
        await interaction.response.edit_message(embed=self.embed, view=self)
        self.stop()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button:discord.ui.Button, interaction:discord.Interaction):
        self.result = True
        self.disable_all_items()
        self.children[0].style = discord.ButtonStyle.gray
        self.embed.title = "Action Confirmed"
        self.embed.colour = discord.Colour.brand_green()
        await interaction.response.edit_message(embed=self.embed, view=self)
        self.stop()


async def send_confirmation(message, user: discord.Member, ctx: discord.ApplicationContext=None, interaction: discord.Interaction=None, ephemeral: bool=None):
    embed = discord.Embed(title="Pending Confirmation", description=message, color=discord.Colour.yellow())
    view = Confirm(user, embed)

    if ctx:
        view.message = await ctx.respond(embed=embed, view=view, ephemeral=ephemeral if ephemeral else True)
    if interaction:
        view.message = await interaction.respond(embed=embed, view=view, ephemeral=ephemeral if ephemeral else True)

    await view.wait()
    return view.result