import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and required validation.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If required variable is not set
    """
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"{key} environment variable is not set")
    return value

def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get environment variable as boolean.

    Args:
        key: Environment variable name
        default: Default boolean value

    Returns:
        Boolean value
    """
    value = os.environ.get(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0) -> int:
    """
    Get environment variable as integer.

    Args:
        key: Environment variable name
        default: Default integer value

    Returns:
        Integer value
    """
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default

def get_env_json(key: str, default: Optional[Any] = None) -> Any:
    """
    Get environment variable as parsed JSON.

    Args:
        key: Environment variable name
        default: Default value if parsing fails

    Returns:
        Parsed JSON value or default
    """
    try:
        value = os.environ.get(key)
        if value:
            return json.loads(value)
        return default
    except (json.JSONDecodeError, TypeError):
        return default


NGROK_URL: Optional[str] = get_env_var('NGROK_URL')
PORT: str = get_env_var('PORT', '3000')

OPENAI_API_KEY: Optional[str] = get_env_var('OPENAI_API_KEY', required=False)
GEMINI_API_KEY: Optional[str] = get_env_var('GEMINI_API_KEY', required=False)
TMDB_API_KEY: str = get_env_var('TMDB_API_KEY', required=True)

SUPPORTS_EXTENSION: bool = get_env_bool('SUPPORTS_EXTENSION', False)
SUPPORTS_LATENCY_TASK_UPDATES: bool = get_env_bool('SUPPORTS_LATENCY_TASK_UPDATES', False)

SKILL_LATENCY: List[Dict[str, Any]] = get_env_json('SKILL_LATENCY', [])

# Default latency configuration for tools
DEFAULT_LATENCY_BY_TOOL: Dict[str, int] = {
    "searchMovies": 2000,
    "searchPeople": 3500
}

if not OPENAI_API_KEY and not GEMINI_API_KEY:
    raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be provided")

def get_skill_latency_config() -> Dict[str, int]:
    """
    Get skill latency configuration, merging defaults with environment settings.

    Returns:
        Dictionary mapping skill names to latency values in milliseconds
    """
    latency_config = DEFAULT_LATENCY_BY_TOOL.copy()

    if SKILL_LATENCY:
        try:
            configured_latency: Dict[str, int] = {}
            for item in SKILL_LATENCY:
                if isinstance(item, dict) and 'skill' in item and 'latency' in item:
                    configured_latency[item['skill']] = item['latency']

            # Merge with defaults, giving priority to configured values
            latency_config.update(configured_latency)
        except Exception:
            # If parsing fails, use defaults
            pass

    return latency_config
