"""
CareFlow Pulse - Configuration Loader

This module handles loading and parsing the agent configuration from YAML files.
Separated from environment variable configuration for clarity.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, TypedDict

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class ServerConfig(TypedDict, total=False):
    """Configuration for a single A2A server."""
    name: str
    port: int
    url: str


class ClientConfig(TypedDict):
    """Client configuration from YAML."""
    system: str


class AgentConfig(TypedDict):
    """Complete agent configuration structure."""
    servers: List[ServerConfig]
    client: ClientConfig


# =============================================================================
# CONFIGURATION LOADER
# =============================================================================

def load_config(config_path: Path | None = None) -> AgentConfig:
    """
    Load agent configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If not provided,
                    searches in current directory and app directory.
    
    Returns:
        Configuration dictionary with servers and client settings
    
    Raises:
        FileNotFoundError: If config file cannot be found
        yaml.YAMLError: If config file is invalid YAML
    """
    try:
        # Find config file
        if config_path is None:
            current_file = Path(__file__).resolve()
            config_path = current_file.parent.parent / 'config.yaml'
            
            if not config_path.exists():
                config_path = Path.cwd() / 'config.yaml'
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        logger.info(f"Loading config from: {config_path}")
        
        with open(config_path, 'r') as f:
            config: Dict[str, Any] = yaml.safe_load(f)
        
        # Override with environment variable if set
        agent_url = os.environ.get("CAREFLOW_AGENT_URL")
        if agent_url:
            config['servers'] = [{"name": "CareFlow Agent", "port": None, "url": agent_url}]
        elif config.get('servers') and config['servers'][0].get('port'):
            # Use port from config if URL not set
            port = config['servers'][0]['port']
            config['servers'] = [{"name": "CareFlow Agent", "port": port, "url": f"http://localhost:{port}"}]
        
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading config.yaml: {e}")
        raise


def get_a2a_server_urls(config: AgentConfig) -> List[str]:
    """
    Extract A2A server URLs from configuration.
    
    Args:
        config: Loaded agent configuration
    
    Returns:
        List of A2A server URLs
    """
    return [
        s.get('url') or f"http://localhost:{s['port']}"
        for s in config.get('servers', [])
        if s.get('url') or s.get('port')
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'load_config',
    'get_a2a_server_urls',
    'AgentConfig',
    'ServerConfig',
    'ClientConfig',
]
