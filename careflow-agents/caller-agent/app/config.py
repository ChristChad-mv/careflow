"""
CareFlow Pulse - Configuration Utilities

Environment variable loading and validation for the Caller Agent.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import os
import json
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load .env file
load_dotenv()


# =============================================================================
# ENVIRONMENT VARIABLE UTILITIES
# =============================================================================

def get_env_var(
    key: str,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Get environment variable with optional default and validation.
    
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
        raise ValueError(f"Required environment variable not set: {key}")
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


# =============================================================================
# CONFIGURATION VALUES
# =============================================================================

# Server Configuration
NGROK_URL: Optional[str] = get_env_var('NGROK_URL')
PORT: str = get_env_var('PORT', '3000')

# API Keys
OPENAI_API_KEY: Optional[str] = get_env_var('OPENAI_API_KEY')
GEMINI_API_KEY: Optional[str] = (
    get_env_var('GEMINI_API_KEY') or 
    get_env_var('GOOGLE_API_KEY')
)

# Feature Flags
SUPPORTS_EXTENSION: bool = get_env_bool('SUPPORTS_EXTENSION', False)
SUPPORTS_LATENCY_TASK_UPDATES: bool = get_env_bool('SUPPORTS_LATENCY_TASK_UPDATES', False)

# Skill Latency Configuration
SKILL_LATENCY: List[Dict[str, Any]] = get_env_json('SKILL_LATENCY', [])

# Validate API keys
if not OPENAI_API_KEY and not GEMINI_API_KEY:
    raise ValueError(
        "At least one API key required: OPENAI_API_KEY or GEMINI_API_KEY/GOOGLE_API_KEY"
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'get_env_var',
    'get_env_bool',
    'get_env_int',
    'get_env_json',
    'NGROK_URL',
    'PORT',
    'OPENAI_API_KEY',
    'GEMINI_API_KEY',
    'SUPPORTS_EXTENSION',
    'SUPPORTS_LATENCY_TASK_UPDATES',
    'SKILL_LATENCY',
]
