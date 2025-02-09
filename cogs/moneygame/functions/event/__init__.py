import discord
from typing import NamedTuple


class Participant(NamedTuple):
    id: int
    name: str


class OneTimeButton(discord.ui.Button):

    def __init__(self, text, max_joins):
        super().__init__(
            style = discord.ButtonStyle.success,
            label = text
        )
        self.max_joins = max_joins


    async def callback(self, interaction):
        if (interaction.user.id, interaction.user.name) in self.view.joiners:
            return await interaction.response.send_message("You already joined!", ephemeral=True)
        
        self.view.joiners.append(Participant(interaction.user.id, interaction.user.name))
        await interaction.response.send_message("You successfully joined!", ephemeral=True)

        if len(self.view.joiners) > self.max_joins:
            self.view.stop()