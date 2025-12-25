import os
import requests
from src.utils.config import TMDB_API_KEY
from typing import Dict, Any
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# TMDB_API_KEY is validated during config import
api_key = TMDB_API_KEY

def call_tmdb_api(endpoint: str, query: str) -> Dict[str, Any]:
    """
    Utility function to call the TMDB API

    Args:
        endpoint: The TMDB API endpoint (e.g., 'movie', 'person')
        query: The search query

    Returns:
        Dict containing the API response data

    Raises:
        ValueError: If TMDB_API_KEY is not set
        Exception: If there's an API error
    """
    try:
        url = f"https://api.themoviedb.org/3/search/{endpoint}"
        params = {
            'api_key': api_key,
            'query': query,
            'include_adult': 'false',
            'language': 'en-US',
            'page': '1'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    except Exception as error:
        logger.error(f"Error calling TMDB API ({endpoint}):", error)
        raise error
