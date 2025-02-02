#   Embed template for Profile menu

import discord
from cogs.moneygame import MoneyItem
from cogs.moneygame.constants import COIN
from utils import progress_bar


class BankBalance(discord.Embed):
    def __init__(self, type:str, amount:int, user):
        super().__init__(
            description = f"{type} {amount:,} coins."
        )

        self.add_field(name="Wallet Balance", value=f"{COIN} `{user.wallet:,}`", inline=False)
        self.add_field(name="Bank Balance", value=f"{COIN} `{user.bank:,}` / `{user.max_bank:,}`")


class EmbedProfile(discord.Embed):
    def __init__(self, name, avatar_url, user):
        progress = user.exp / (25 * (user.level+1))
        bar = progress_bar(progress, 6)
        super().__init__(
            description = (
                f"## {name}\n"
                f"` {user.level} `{bar}\n"
                f"-# EXP: {user.exp} / {25 * (user.level+1)}"
            )
        )
        self.description = self.description.replace('@', '\u25B0')
        self.description = self.description.replace('^', '\u25B1')

        self.add_field(
            name = "Money",
            value = (
                f"{COIN} `{user.wallet:,}`\n"
                f"🏦 `{user.bank:,}`\n"
                f"Total: `{(user.wallet + user.bank):,}`"
            )
        )

        self.add_field(
            name = "Bonus",
            value = f"* +{round((user.coin_multi - 1) * 100)}% cash",
            inline = True
        )

        if user.active_items:
            self.add_field(
                name = "Active Items",
                value = '\n'.join([
                    f"* {MoneyItem.from_id(int(str_item_id)).emoji} **{MoneyItem.from_id(int(str_item_id)).name}** "
                    f"expires <t:{expire_time}:R> (<t:{expire_time}:t>)"
                    for str_item_id, expire_time in user.active_items.items()
                ]),
                inline = False
            )

        self.set_thumbnail(url=avatar_url)


class Inventory(discord.Embed):
    def __init__(self, items: dict):
        super().__init__(description="")

        self.items = items
        if self.items == {}:
            self.description = "No items"
            return
        
        sorted_items = self.sort_items_into_list()
        for item, amount in sorted_items:
            self.description += (f"{item.emoji} **{item.name}** - ` {amount} `\n\n")
            
        self.description = self.description[:-2] # remove extra line breaks


    def sort_items_into_list(self):   
        item_list = []
        for item_id, amount in self.items.items():
            item = MoneyItem.from_id(item_id)
            if not item:
                continue
            
            item_list.append((item, amount))

        return sorted(item_list, key=lambda x:x[0].name)


class ItemInfo(discord.Embed):
    def __init__(self, item:MoneyItem, amount:int):
        super().__init__(
            title = f"{item.name} ({amount})",
            description = f"> *{item.description}*\n\n{item.use}"
        )
        self.add_field(name="Sell for", value=f"{COIN} `{item.sell_price:,}`")
        self.set_footer(text=f"{item.rarity} {item.type}")
        self.set_thumbnail(url=discord.PartialEmoji.from_str(item.emoji).url)

class SingleItemMessage(discord.Embed):
    def __init__(self, message:str, item:MoneyItem):
        article = "an" if item.name[0] in "AEIOUaeiou" else "a"
        super().__init__(
            description = f"You used {article} {item.emoji} **{item.name}**!\n* {message}"
        )