import os
from dotenv import load_dotenv
import requests
import json
import random
from utils import logger

load_dotenv()
URL = os.environ['GIST_URL']

class ImageCommand:



    @staticmethod
    def get_random_image(tag):
        response = requests.get(URL)

        if response.status_code == 200:
            images = response.json()  # Convert JSON response to Python dictionary
        else:
            logger.error(f"Failed to fetch JSON: {response.status_code}")

        if tag.lower() in ['lati', 'eonduo']:
            target_types = {"latios", "latias"}
        else:
            target_types = {tag.lower()}

        # Filter using lambda to check intersection
        filtered_images = list(filter(lambda img: set(img['tags']) & target_types, images))

        if not filtered_images:
            logger.warning(f"No images found for tag: {tag}")
            return None

        return random.choice(filtered_images)
