import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import agent
from executor import CallerAgentExecutor, caller_agent_card
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    # Initialize the executor with our Agent instance
    executor = CallerAgentExecutor(agent)
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(executor, task_store)

    # Create the A2A Starlette application
    a2a_app = A2AStarletteApplication(
        agent_card=caller_agent_card,
        http_handler=request_handler
    ).build()

    return a2a_app

# Create the app
app = create_app()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🚀 Caller Agent A2A Server running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
