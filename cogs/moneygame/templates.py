#   Embed template for Profile menu

import discord

class EmbedProfile(discord.Embed):
    def __init__(self, user, data):
        data.load_all()
        length = 8
        progress = int(length * (data._exp / ((data._level+1) * 25)))
        super().__init__(
            description = (
                f"## {user.display_name}\n"
                f"` {data._level} ` {'@' * progress}{'^' * (length - progress)}\n"
                f"-# NEXT LEVEL: {25 * (data._level + 1) - data._exp}XP"
            )
        )
        self.set_thumbnail(url=user.avatar.url),
        self.description = self.description.replace('@', '\u25B0')
        self.description = self.description.replace('^', '\u25B1')
        self.add_field(
            name = "Money",
            value = (
                f"💵 $ {data._wallet:,}\n"
                f"🏦 $ {data._bank:,}\n"
                f"$ {(data._wallet + data._bank):,} total"
            )
        )
        self.add_field(
            name = "Bonus",
            value = f"* +{round((data.calculate_cash_multi() - 1) * 100)}% cash",
            inline = True
        )