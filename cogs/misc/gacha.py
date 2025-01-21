import random
import discord

class Delivery(discord.ui.View):
    def __init__(self, user: discord.User, embed):
        super().__init__(timeout=30)
        self.user = user
        self.embed = embed
        self.rolls = [0, 0, 0, 0]
        self.names = [
            "Target",
            "Rare Gift",
            "Uncommon Gift",
            "Common Gift"
        ]
        self.emoji = [
            "<:RedGift:1331175787289776179>", 
            "<:RainbowGift:1331176034740994050>",
            "<:GoldGIft:1331175762497372240>", 
            "<:GreenGift:1331176032367149127>"
        ]
        self.rates = [1, 4, 15, 80]

    def edit_original_embed(self):
        self.embed.description = f"{self.user.mention}'s rolls: {sum(self.rolls)}\n"
        for i in range(4):
            self.embed.description += f"* {self.rolls[i]}x {self.emoji[i]} {self.names[i]}\n"

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("You cannot use these buttons", ephemeral=True)
            return False
        else:
            return True
        
    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(view=self)
        self.stop()

    @discord.ui.button(label="Roll 1x", style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji.from_str("<:Item306:1328713790501421077>"))
    async def rollone(self, button:discord.ui.Button, interaction:discord.Interaction):
        chance = random.random()

        if chance < 0.01:
            self.rolls[0] += 1
            text = self.emoji[0]
        elif chance < 0.05:
            self.rolls[1] += 1
            text = self.emoji[1]
        elif chance < 0.2:
            self.rolls[2] += 1
            text = self.emoji[2]
        else:
            self.rolls[3] += 1
            text = self.emoji[3]

        self.edit_original_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)
        await interaction.followup.send(embed=discord.Embed(description="Pelipper has returned with:\n# {text}"), ephemeral=True)

    @discord.ui.button(label="Roll 10x", style=discord.ButtonStyle.primary, emoji=discord.PartialEmoji.from_str("<:Item309:1328714395651670166>"))
    async def rollten(self, button:discord.ui.Button, interaction:discord.Interaction):
        text = "Pelipper has returned with:\n## "
        for i in range(11):
            chance = random.random()

            if chance < 0.01:
                self.rolls[0] += 1
                text += self.emoji[0]
            elif chance < 0.05:
                self.rolls[1] += 1
                text += self.emoji[1]
            elif chance < 0.2:
                self.rolls[2] += 1
                text += self.emoji[2]
            else:
                self.rolls[3] += 1
                text += self.emoji[3]

            if i == 4:
                text += "\n## "

        self.edit_original_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)
        await interaction.followup.send(embed=discord.Embed(description=text), ephemeral=True)

    @discord.ui.button(label="View Chances")
    async def chances(self, button:discord.ui.Button, interaction:discord.Interaction):
        text = ""
        for i in range(4):
            text += f"* `{self.rates[i]}%` {self.emoji[i]} {self.names[i]}\n"
        await interaction.response.send_message(embed=discord.Embed(title="Chances", description=text), ephemeral=True)
