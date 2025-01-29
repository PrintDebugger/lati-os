import discord

class ConfirmAction(discord.ui.View):
    def __init__(self, sender:discord.Member, embed):
        super().__init__(timeout=30)
        self.sender = sender
        self.embed = embed
        self.result = False

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.sender:
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


class ConfirmEmbed(discord.Embed):
    
    def __init__(self, message, *fields: tuple):
        super().__init__(
            title = "Pending Confirmation",
            description = message,
            color = discord.Colour.yellow()
        )

        for name, value, inline in fields:
            self.add_field(name=name, value=value, inline=inline)