"""
CareFlow Pulse - Configuration Utilities

Environment variable loading and validation for the Pulse Agent.
"""

"""
Configuration Loader
Centralized environment variable management for Pulse Agent.
"""
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable not set: {key}")
    return value

# Server Configuration
PORT = int(os.getenv("PORT", "8080"))
SERVICE_URL: str = get_env_var('SERVICE_URL', 'http://localhost:8000/')

# Agent Configuration
AGENT_NAME: str = "careflow_pulse_agent"
AGENT_MODEL: str = get_env_var('AGENT_MODEL', 'gemini-3-pro-preview')
HOSPITAL_ID: str = get_env_var('HOSPITAL_ID', 'HOSP001')

# External Services
CAREFLOW_CALLER_URL: str = get_env_var('CAREFLOW_CALLER_URL', 'http://localhost:8080')
MCP_TOOLBOX_URL: str = get_env_var('MCP_TOOLBOX_URL', 'http://127.0.0.1:5000')

# API Keys
GOOGLE_API_KEY: Optional[str] = get_env_var('GOOGLE_API_KEY')

# Telemetry
OTLP_ENDPOINT: str = get_env_var('OTLP_ENDPOINT', 'http://localhost:4317')
DEPLOYMENT_ENV: str = get_env_var('DEPLOYMENT_ENV', 'development')

__all__ = [
    'PORT',
    'SERVICE_URL',
    'AGENT_NAME',
    'AGENT_MODEL',
    'HOSPITAL_ID',
    'CAREFLOW_CALLER_URL',
    'MCP_TOOLBOX_URL',
    'GOOGLE_API_KEY',
    'OTLP_ENDPOINT',
    'DEPLOYMENT_ENV'
]
