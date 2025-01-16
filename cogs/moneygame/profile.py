#   Embed template for Profile menu

import discord

class EmbedProfile(discord.Embed):
    def __init__(self, user, data):
        length = 8
        progress = int(length * (data.exp / ((data.level+1) * 25)))
        super().__init__(
            thumbnail = discord.EmbedMedia(url=user.avatar.url),
            description = (
                f"## {data.name}\n"
                f"` {data.level} ` {'@' * progress}{'^' * (length - progress)}\n"
                f"-# NEXT LEVEL: {25 * (data.level + 1) - data.exp}XP\n\n"
                f"-# MONEY\n"
                f"💵 $ {data.wallet:,}\n"
                f"🏦 $ {data.bank:,}\n"
                f"$ {(data.wallet + data.bank):,} total"
            )
        )
        self.description = self.description.replace('@', '\u25B0')
        self.description = self.description.replace('^', '\u25B1')