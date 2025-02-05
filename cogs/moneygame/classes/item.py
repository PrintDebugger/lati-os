import json
import discord

from ..config import PATH_ITEMDATA
from utils import logger


class MoneyItem:
    _item_metadata = None
    _data_loaded = False

    @classmethod
    def _load_data(cls):
        """Loads json metadata once and cache it"""
        if not cls._data_loaded:
            try:
                with open(PATH_ITEMDATA, 'r') as file:
                    cls._item_metadata = json.load(file)
                    cls._data_loaded = True
            except Exception:
                    logger.exception(f"Error loading {PATH_ITEMDATA}")


    #   Create Item class based on item_id
    @classmethod
    def from_id(cls, item_id):
        item_id = str(item_id)

        cls._load_data()

        if not cls._item_metadata:
            return None
        
        try:
            data = cls._item_metadata[item_id]
        except KeyError:
            logger.error(f"KeyError: item_id {item_id} does not exist")
            return None

        try:
            item = cls()
            item.id = item_id
            item.name = data['name']
            item.emoji = data['emoji']
            item.use = data['use']
            item.description = data['description']
            item.sell_price = data['sell']
            item.rarity = data['rarity']
            item.type = data['type']
            return item
        except KeyError:
            logger.exception(f"KeyError in item_id {item_id}")
            return None

    @classmethod
    def from_name(cls, name: str):
        cls._load_data()

        if not cls._item_metadata:
            return None
        
        for item_id, data in cls._item_metadata.items():
            if data['name'] == name:
                return cls.from_id(item_id)
            
        logger.error(f"No item found with name {name}")
        return None
    
    @classmethod
    def get_matching_items(cls, ctx:discord.AutocompleteContext):
        '''Returns a list of matching item names based on user input.'''
        cls._load_data()

        if not cls._item_metadata:
            logger.warning("Item metadata is empty")
            return []
        
        all_names = sorted([
            data['name']
            for data in cls._item_metadata.values()
            if 'name' in data
        ])
        
        user_input = ctx.value.lower().replace(' ', '')
        matches = [
            name
            for name in all_names
            if user_input in str(name).lower().replace(' ', '')
        ][:25]

        return matches
