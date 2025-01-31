import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_USER = os.environ['SIGHTENGINE_API_USER']
API_SECRET = os.environ['SIGHTENGINE_API_SECRET']

def detect_ai(image_url: str):
    from utils import log
    
    try:
        response = requests.get(
            'https://api.sightengine.com/1.0/check.json',
            params={
                'models': 'genai',
                'api_user': API_USER,
                'api_secret': API_SECRET,
                'url': image_url
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        log.exception("Exception in 'sightengine.py'")
        return None