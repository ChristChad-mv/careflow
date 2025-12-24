# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from fastapi import FastAPI
from google.cloud import logging as google_cloud_logging

from app.agent import root_agent
from app.app_utils.executor.a2a_agent_executor import (
    LangGraphAgentExecutor,
)
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

setup_telemetry()

request_handler = DefaultRequestHandler(
    agent_executor=LangGraphAgentExecutor(graph=root_agent),
    task_store=InMemoryTaskStore(),
)

A2A_RPC_PATH = "/a2a/app"


def build_agent_card() -> AgentCard:
    """Builds the Agent Card for the LangGraph agent."""
    skill = AgentSkill(
        id="root_agent-get_weather",
        name="get_weather",
        description="Simulates a web search. Use it get information on weather.",
        tags=["llm", "tools"],
        examples=["What's the weather in San Francisco?"],
    )
    agent_card = AgentCard(
        name="root_agent",
        description="API for interacting with the Agent caller-agent",
        url=f"{os.getenv('APP_URL', 'http://0.0.0.0:8000')}{A2A_RPC_PATH}",
        version=os.getenv("AGENT_VERSION", "0.1.0"),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
    return agent_card


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
    agent_card = build_agent_card()
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app_instance,
        agent_card_url=f"{A2A_RPC_PATH}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=A2A_RPC_PATH,
        extended_agent_card_url=f"{A2A_RPC_PATH}{EXTENDED_AGENT_CARD_PATH}",
    )
    yield


# Initialize FastAPI app and logging
app = FastAPI(
    title="caller-agent",
    description="API for interacting with the Agent caller-agent",
    lifespan=lifespan,
)

logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
