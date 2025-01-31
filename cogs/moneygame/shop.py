import json
import discord

from cogs.moneygame import MoneyItem
from cogs.moneygame.constants import PATH_SHOPDATA, COIN
from interactions import ConfirmAction, ConfirmEmbed
from utils import logger


def get_shop_listing():
    try:
        with open(PATH_SHOPDATA, 'r') as file:
            data = json.load(file)
    except Exception:
        logger.exception(f"Error loading {PATH_SHOPDATA}")
        return []

    shop_listing = []
    for item_id, price in data.items():
        shop_listing.append((int(item_id), price))

    return shop_listing


class ShopEmbed(discord.Embed):

    def __init__(self, user):
        super().__init__(description = f"## {COIN} {user.wallet:,}\n‎\n")

        shop_listing = get_shop_listing()
        if not shop_listing:
            self.description += "*There are currently no items available.*"
            logger.warning("Shop items empty")
            return
        
        for item_id, price in shop_listing:
            item = MoneyItem.from_id(item_id)
            self.description += (
                f"{item.emoji} **{item.name}** -{COIN} `{price}`\n*{item.use}*\n\n"
            )
        
        self.description = self.description[:-2] # remove extra line breaks


class BuyButton(discord.ui.Button):

    def __init__(self, sender, item_id, price, user):
        self.sender = sender
        self.price = price
        self.item_id = item_id
        self.item = MoneyItem.from_id(item_id)
        self.user = user # Not to be mistaken with discord.User!!!

        super().__init__(
            style = discord.ButtonStyle.primary,
            label = "Buy",
            emoji = discord.PartialEmoji.from_str(self.item.emoji),
            disabled = self.user.wallet < price
        )

    async def callback(self, interaction):
        embed = ConfirmEmbed(f"Buy 1 {self.item.emoji} **{self.item.name}** for {self.price:,} coins?")
        view = ConfirmAction(self.sender, embed)
        view.message = await interaction.response.send_message(self.sender.mention, embed=embed, view=view, ephemeral=True)
        await view.wait()
        if not view.result:
            return
        await self.user.add_wallet(- self.price)
        await self.user.add_item(self.item_id, 1)
        await self.view.message.edit(embed=ShopEmbed(self.user), view=Shop(self.sender, self.user))
        await interaction.followup.send(f"You bought 1 {self.item.emoji} **{self.item.name}**!", ephemeral=True)


class Shop(discord.ui.View):

    def __init__(self, sender, user):
        super().__init__(timeout=30)
        self.sender = sender

        shop_listing = get_shop_listing()
        for item_id, price in shop_listing:
            self.add_item(BuyButton(self.sender, item_id, price, user))

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.sender:
            await interaction.response.send_message("You cannot use these buttons", ephemeral=True)
            return False
        else:
            return True