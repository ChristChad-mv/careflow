import json
from src.utils.config import get_skill_latency_config
import time
import asyncio
from typing import Any, TypeVar, Callable, Coroutine
from langchain_core.tools import tool # type: ignore[import]
from pydantic import BaseModel, Field
from src.server.tmdb import call_tmdb_api
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get skill latency configuration from config module
latecy_by_tools = get_skill_latency_config()
logger.info(f"[Tools] Loaded skill latency configuration: {latecy_by_tools}")

# Schema for searchMovies
class MovieSearchInput(BaseModel):
    query: str = Field(description="The movie title to search for")

# Schema for searchPeople
class PeopleSearchInput(BaseModel):
    query: str = Field(description="The person's name to search for")

# Helper function to create synthetic delay
async def create_synthetic_delay(tool_name: str) -> None:
    latency = latecy_by_tools.get(tool_name, 0)
    if latency and latency > 0:
        logger.info(f"[Tools] Setting {latency}ms minimum execution time for {tool_name}")
        await asyncio.sleep(latency / 1000)  # Convert ms to seconds
    return

T = TypeVar('T')

# Helper function to execute with minimum latency
async def execute_with_minimum_latency(tool_name: str, operation: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """Execute an operation with a guaranteed minimum latency."""
    start_time = time.time()
    delay_task = asyncio.create_task(create_synthetic_delay(tool_name))

    try:
        # Run the operation
        operation_task = asyncio.create_task(operation())
        # Wait for both tasks to complete
        result = await operation_task
        await delay_task

        actual_duration = (time.time() - start_time) * 1000  # Convert to ms
        configured_latency = latecy_by_tools.get(tool_name, 0)

        if configured_latency > 0:
            logger.info(f"[Tools] {tool_name} completed in {actual_duration:.2f}ms (minimum: {configured_latency}ms)")

        return result
    except Exception as error:
        # Still wait for the minimum delay even if the operation fails
        await delay_task
        raise error

@tool("searchMovies", args_schema=MovieSearchInput)
async def search_movies(query: str) -> str:
    """Search TMDB for movies by title"""
    logger.info(f"[tmdb:searchMovies] {json.dumps(query)}")

    async def _search_operation():
        try:
            data = call_tmdb_api('movie', query)

            # Only modify image paths to be full URLs
            results = []
            for movie in data.get('results', []):
                if movie.get('poster_path'):
                    movie['poster_path'] = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                if movie.get('backdrop_path'):
                    movie['backdrop_path'] = f"https://image.tmdb.org/t/p/w500{movie['backdrop_path']}"
                results.append(movie)

            # Update the results in the response
            data['results'] = results

            return json.dumps(data)
        except Exception as error:
            logger.info(f'Error searching movies: {error}')
            raise error

    return await execute_with_minimum_latency('searchMovies', _search_operation)

@tool("searchPeople", args_schema=PeopleSearchInput)
async def search_people(query: str) -> str:
    """Search TMDB for people by name"""
    logger.info(f"[tmdb:searchPeople] {json.dumps(query)}")

    async def _search_operation():
        try:
            data = call_tmdb_api('person', query)

            # Only modify image paths to be full URLs
            results = []
            for person in data.get('results', []):
                # Update profile path
                if person.get('profile_path'):
                    person['profile_path'] = f"https://image.tmdb.org/t/p/w500{person['profile_path']}"

                # Also modify poster paths in known_for works
                if person.get('known_for') and isinstance(person['known_for'], list):
                    for work in person['known_for']:
                        if work.get('poster_path'):
                            work['poster_path'] = f"https://image.tmdb.org/t/p/w500{work['poster_path']}"
                        if work.get('backdrop_path'):
                            work['backdrop_path'] = f"https://image.tmdb.org/t/p/w500{work['backdrop_path']}"

                results.append(person)

            # Update the results in the response
            data['results'] = results

            return json.dumps(data)
        except Exception as error:
            logger.info(f'Error searching people: {error}')
            raise error

    return await execute_with_minimum_latency('searchPeople', _search_operation)
