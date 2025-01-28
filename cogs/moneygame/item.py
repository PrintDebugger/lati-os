import json
from cogs.moneygame.constants import PATH_ITEMDATA

class MoneyItem:
    _item_metadata_cache = None
    _data_loaded = False

    @classmethod
    def _load_data(cls):
        """Loads json metadata once and cache it"""
        if not cls._data_loaded:
            with open(PATH_ITEMDATA, 'r') as file:
                try:
                    cls._item_metadata_cache = json.load(file)
                    print("DEBUG: Loaded items:", cls._item_metadata_cache.keys())
                    cls._data_loaded = True
                except FileNotFoundError:
                    print(f"FileNotFoundError: Path {PATH_ITEMDATA} does not exist")
                    cls._item_metadata_cache = {}
                except json.JSONDecodeError:
                    print(f"JSONDecodeError: Invalid JSON in {PATH_ITEMDATA}")
                    cls._item_metadata_cache = {}
                except Exception as e:
                    print(f"Unexpected error loading {PATH_ITEMDATA}: {str(e)}")
                    cls._item_metadata_cache = {}

    #   Create Item class based on item_id
    @classmethod
    def from_id(cls, item_id: int):
        cls._load_data()

        if not cls._item_metadata_cache:
            return None
        
        try:
            data = cls._item_metadata_cache[str(item_id)]
        except KeyError:
            print(f"KeyError: item_id {item_id} does not exist")
            return None

        try:
            item = cls()
            item.id = item_id
            item.name = data['name']
            item.use = data['use']
            item.description = data['description']
            item.sell_price = data['sell']
            item.rarity = data['rarity']
            item.type = data['type']
            return item
        except KeyError as e:
            print(f"KeyError in item_id {item_id}: {str(e)}")
            return None