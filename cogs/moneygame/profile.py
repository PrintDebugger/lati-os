#   Embed template for Profile menu

import discord

class EmbedProfile(discord.Embed):
    def __init__(self, user, data):
        length = 8
        progress = int(length * (data.exp / ((data.level+1) * 25)))
        super().__init__(
            description = (
                f"## {data.name}\n"
                f"` {data.level} ` {'@' * progress}{'^' * (length - progress)}\n"
                f"-# NEXT LEVEL: {25 * (data.level + 1) - data.exp}XP"
            )
        )
        self.set_thumbnail(url=user.avatar.url),
        self.description = self.description.replace('@', '\u25B0')
        self.description = self.description.replace('^', '\u25B1')
        self.add_field(
            name = "Money",
            value = (
                f"💵 $ {data.wallet:,}\n"
                f"🏦 $ {data.bank:,}\n"
                f"$ {(data.wallet + data.bank):,} total"
            )
        )
        self.add_field(
            name = "Bonus",
            value = f"* +{round((data.cash_multi - 1) * 100)}% cash",
            inline = True
        )