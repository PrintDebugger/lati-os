import os
from dotenv import load_dotenv
import requests
import random
import discord
from utils import logger

load_dotenv()

class ImageCommand:
    URL = os.environ['GIST_URL']
    _images = []


    @classmethod
    def _fetch_data(cls):
        headers = {"user-agent": "Mozilla/5.0"}
        try:
            response = requests.get(cls.URL, headers=headers, timeout=5)
            cls._images = response.json()
            return cls._images
        except requests.RequestException:
            logger.exception("Request failed")

        return cls._images


    @classmethod
    def get_random_image(cls, tag):
        cls._fetch_data()

        target_types = {tag.lower()}

        filtered_images = [i for i in cls._images if any(t in target_types for t in i['tags'])]

        if not filtered_images:
            logger.warning(f"No images found for tag: {tag}")
            return {}

        return random.choice(filtered_images)


    @classmethod
    def get_all_tags(cls, ctx:discord.AutocompleteContext):
        cls._fetch_data()

        if not cls._images:
            logger.warning("No images")
            return []
        
        all_tags = set()
        for img in cls._images:
            all_tags.update(img['tags'])
        all_tags = sorted(all_tags)
        
        user_input = ctx.value.lower().replace(' ', '')
        matches = [
            t
            for t in all_tags
            if user_input in t
        ][:25]

        return matches