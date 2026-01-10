"""
CareFlow Pulse Server
A2A Protocol Backend Entry Point.
"""
import os
import logging
import httpx
import uvicorn
import argparse
import sys

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.inmemory_push_notification_config_store import InMemoryPushNotificationConfigStore
from a2a.server.tasks.base_push_notification_sender import BasePushNotificationSender

# Modularized Imports
from .app_utils.config_loader import PORT, AGENT_NAME
from .app_utils.telemetry import setup_telemetry
from .agent import root_agent
from .app_utils.executor.careflow_executor import CareFlowAgentExecutor
from .schemas.agent_card.v1.careflow_card import get_pulse_agent_card

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """
    Initializes and returns the A2A Starlette application.
    """
    # 1. Initialize Executor and Stores
    executor = CareFlowAgentExecutor(root_agent)
    task_store = InMemoryTaskStore()
    push_config_store = InMemoryPushNotificationConfigStore()
    
    # 2. Setup Push Notifications
    http_client = httpx.AsyncClient()
    push_sender = BasePushNotificationSender(http_client, push_config_store)
    
    # 3. Initialize Request Handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        push_config_store=push_config_store,
        push_sender=push_sender
    )

    # 4. Create App with Agent Card
    app = A2AStarletteApplication(
        agent_card=get_pulse_agent_card(),
        http_handler=request_handler
    )
    
    starlette_app = app.build()

    # 5. Configure Telemetry
    setup_telemetry(starlette_app, service_name=AGENT_NAME)

    return starlette_app

app = create_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CareFlow Pulse Agent Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    args = parser.parse_args()

    # Priority: Command Line > Config > Default
    run_port = args.port or int(PORT)
    
    logger.info(f"Starting CareFlow A2A Server on port {run_port}")
    uvicorn.run(app, host="0.0.0.0", port=run_port)
