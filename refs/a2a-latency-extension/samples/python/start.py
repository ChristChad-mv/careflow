#!/usr/bin/env python3
import os
import sys
import subprocess
import yaml
from typing import List, Optional, TypedDict, Dict
import json
import argparse
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerCmd(TypedDict):
    name: str
    command: str
    color: str
    env: Dict[str, str]
    silent: Optional[bool]


class SkillLatency(TypedDict):
    skill: str
    latency: int


class NgrokConfig(TypedDict):
    url: str


class ClientConfig(TypedDict):
    port: int
    supportsLatencyTaskUpdates: bool
    ngrok: Optional[NgrokConfig]
    system: str


class ServerConfig(TypedDict):
    name: str
    port: int
    supportsLatencyTaskUpdates: Optional[bool]
    skillLatency: Optional[List[SkillLatency]]


class Config(TypedDict):
    client: ClientConfig
    servers: List[ServerConfig]


CONFIG_FILE = 'config.yaml'


def get_config_file() -> str:
    """Parse command line arguments for --config flag."""
    parser = argparse.ArgumentParser(description='Start client and server processes')
    parser.add_argument('--config', type=str, default=CONFIG_FILE,
                       help=f'Config file path (default: {CONFIG_FILE})')
    args = parser.parse_args()
    return args.config


def main() -> None:
    config_file = get_config_file()

    # Check if config file exists
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} not found!")
        sys.exit(1)

    try:
        # Read and parse the YAML configuration
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)

        if not config.get('servers') or len(config['servers']) == 0:
            logger.info('No servers configured in config.yaml')
            sys.exit(1)

        # Build commands for client and server
        commands: List[ServerCmd] = []

        # Client command (voice.py)
        client_cmd = "python ./src/client/voice.py"

        # Set environment variables for client configuration
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd()
        env['PORT'] = str(config['client']['port'])
        if config['client'].get('supportsLatencyTaskUpdates'):
            env['SUPPORTS_LATENCY_TASK_UPDATES'] = 'true'
        if config['client'].get('ngrok', {}).get('url'):
            env['NGROK_URL'] = config['client']['ngrok']['url']

        commands.append({
            'command': client_cmd,
            'name': 'Client',
            'env': env,
            'color': 'green',
            'silent': False
        })

        # Add commands for all servers
        server_colors = ['blue', 'cyan', 'magenta', 'yellow']
        for i, server in enumerate(config['servers']):
            server_cmd = "python ./src/server/app.py"

            # Set environment variables for the server
            server_env = os.environ.copy()
            server_env['PYTHONPATH'] = os.getcwd()
            server_env['PORT'] = str(server['port'])
            if server.get('supportsLatencyTaskUpdates'):
                server_env['SUPPORTS_LATENCY_TASK_UPDATES'] = 'true'
            if server.get('supportsExtension'):
                server_env['SUPPORTS_EXTENSION'] = 'true'
            if server.get('skillLatency'):
                server_env['SKILL_LATENCY'] = json.dumps(server['skillLatency'])

            commands.append({
                'command': server_cmd,
                'name': server['name'],
                'env': server_env,
                'color': server_colors[i % len(server_colors)],
                'silent': server.get('silent', False)
            })

        # Add ngrok command last if configured
        if config['client'].get('ngrok', {}).get('url'):
            # Use ngrok with explicit domain flag for better compatibility
            ngrok_cmd = f"ngrok http {config['client']['port']} --domain={config['client']['ngrok']['url']}"
            commands.append({
                'command': ngrok_cmd,
                'name': 'ngrok',
                'env': os.environ.copy(),
                'color': 'yellow',
                'silent': True
            })
            logger.info(f"🔗 Starting ngrok tunnel: {config['client']['ngrok']['url']} -> localhost:{config['client']['port']}")

        logger.info(f"Starting client and server{'s' if len(config['servers']) > 1 else ''}...")
        logger.info(f"Client port: {config['client']['port']}")
        for i, server in enumerate(config['servers']):
            logger.info(f"Server {i + 1} ({server['name']}) port: {server['port']}")

        if config['client'].get('ngrok', {}).get('url'):
            logger.info(f"ngrok URL: {config['client']['ngrok']['url']}")

        # Start all processes
        logger.info('Starting client and server processes...')
        processes: List[tuple[subprocess.Popen[bytes], str]] = []

        try:
            for cmd_info in commands:
                logger.info('Running command', cmd_info)

                # Configure output redirection based on silent flag
                stdout = subprocess.DEVNULL if cmd_info.get('silent', False) else None
                stderr = subprocess.DEVNULL if cmd_info.get('silent', False) else None

                process = subprocess.Popen(
                    cmd_info['command'],
                    shell=True,
                    env=cmd_info['env'],
                    stdout=stdout,
                    stderr=stderr
                )
                processes.append((process, cmd_info['name']))
                logger.info(f"Started {cmd_info['name']} process")

            # Wait for all processes
            logger.info("All processes started. Press Ctrl+C to terminate.")

            # Keep the main thread alive
            for process, name in processes:
                process.wait()

        except KeyboardInterrupt:
            logger.info('\nReceived Ctrl+C, shutting down gracefully...')
        finally:
            # Terminate all processes
            for process, name in processes:
                if process.poll() is None:  # If process is still running
                    logger.info(f"Terminating {name} process...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.info(f"Killing {name} process...")
                        process.kill()

            logger.info("All processes terminated")

    except Exception as error:
        logger.error('Error reading or parsing config file:', error)
        sys.exit(1)


# Handle process termination
if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.error('Unexpected error:', error)
        sys.exit(1)
