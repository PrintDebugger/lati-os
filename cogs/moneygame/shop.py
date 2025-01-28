import json
import discord

from cogs.moneygame import MoneyItem
from cogs.moneygame.constants import PATH_SHOPDATA
from interactions import send_confirmation

def get_shop_listing():
    try:
        with open(PATH_SHOPDATA, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"FileNotFoundError: Path {PATH_SHOPDATA} does not exist")
        return []
    except json.JSONDecodeError:
        print(f"JSONDecodeError: Invalid JSON in {PATH_SHOPDATA}")
        return []
    except Exception as e:
        print(f"Unexpected error loading {PATH_SHOPDATA}: {str(e)}")
        return []

    shop_listing = []
    for item_id, price in data.items():
        shop_listing.append((int(item_id), price))

    return shop_listing


class ShopEmbed(discord.Embed):

    def __init__(self, user):
        super().__init__(description = f"You have **${user.wallet:,}**\n\n")

        shop_listing = get_shop_listing()
        if not shop_listing:
            self.description += "*There are currently no items available.*"
            return
        
        for item_id, price in shop_listing:
            item = MoneyItem.from_id(item_id)
            self.description += (
                f"**{item.name}** ` $ {price} `\n*{item.use}*\n\n"
            )
        
        self.description = self.description[:-2]


class BuyButton(discord.ui.Button):

    def __init__(self, sender, item_id, price, user):
        self.interaction_user = sender
        self.price = price
        self.item_id = item_id
        self.item_name = MoneyItem.from_id(item_id).name
        self.user = user # Not to be mistaken with discord.User!!!
        super().__init__(
            style = discord.ButtonStyle.primary,
            label = f"Buy {self.item_name}"
        )

        if user.wallet < price:
            self.disabled = True

    async def callback(self, interaction):
        result = await send_confirmation(
            f"Buy **{self.item_name}** for ${self.price}?",
            user = interaction.user,
            interaction = interaction
        )
        if result:
            await interaction.respond(f"You bought 1 **{self.item_name}**!", ephemeral=True)
            await interaction.edit(embed=ShopEmbed(self.user), view=Shop(self.interaction_user, self.user))
            await self.user.add_wallet(- self.price)
            await self.user.add_item(self.item_id, 1)


class Shop(discord.ui.View):

    def __init__(self, sender, user):
        super().__init__(timeout=30)
        self.ctx_user = sender

        shop_listing = get_shop_listing()
        for item_id, price in shop_listing:
            self.add_item(BuyButton(sender, item_id, price, user))

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != interaction.user:
            await interaction.response.send_message("You cannot use these buttons", ephemeral=True)
            return False
        else:
            return True