import json

from cogs.moneygame.constants import PATH_RNGDATA
from utils import logger


class LuckHandler:
    _rng_data = None
    _data_loaded = False

    @classmethod
    def _load_data(cls):
        """Loads json metadata once and cache it"""
        if not cls._data_loaded:
            try:
                with open(PATH_RNGDATA, 'r') as file:
                    cls._rng_data = json.load(file)
                    cls._data_loaded = True
            except Exception:
                    logger.exception(f"Error loading {PATH_RNGDATA}")


    @classmethod
    def get_outcome(cls, type:str, chance:float):
        """Returns a dict of the outcome, 
        and a boolean indicating whether it is a success 
        based on a randomly generated float."""
        cls._load_data()
        if not cls._rng_data:
            logger.error("RNG data is empty")
            return None
        
        if not type in cls._rng_data:
            logger.error(f"No rng data for type {type}")
            return None
        
        outcome = cls()
        outcome.success = False
        outcome.info = {}

        remaining_chance = 1
        for x in cls._rng_data[type]['outcomes']:
            remaining_chance = remaining_chance - x['chance'] # subtract chance thresholds 
            if chance > remaining_chance:
                outcome.success = True
                outcome.info = x
                break
        
        return outcome