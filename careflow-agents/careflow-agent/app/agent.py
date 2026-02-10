"""
CareFlow Pulse Agent Definition
Entry point for the ADK-powered orchestration layer.
"""
import sys
import os
import logging
from typing import AsyncGenerator, Any

from pydantic import Field
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from a2a.types import Message
from a2a.server.agent_execution import RequestContext
from app.schemas.agent_card.v1.careflow_card import get_pulse_agent_card
import google.genai.types as genai_types
from google.adk.planners import BuiltInPlanner

# Modularized Imports
from app.app_utils.config_loader import (
    AGENT_NAME, 
    AGENT_MODEL, 
    HOSPITAL_ID
)
from app.app_utils.prompts.system_prompts import CAREFLOW_SYSTEM_PROMPT
from app.tools import mcp__tool_loader
from app.tools.a2a_tools import a2a_tools
from app.tools.retry_tools import retry_tools
from app.tools.interaction_logger import interaction_tools
from app.tools.clinical_tools import clinical_tools
from app.tools.schedule_tools import schedule_tools


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize MCP tools immediately
mcp__tool_loader.init_mcp_tools()

AGENT_DESCRIPTION = "An AI agent that monitors post-hospitalization patients, analyzes symptoms, and generates alerts for healthcare coordinators."

class CareFlowAgent(BaseAgent):
    """
    Custom CareFlow Agent following the user's VoiceAgent pattern.
    Wraps an internal LlmAgent and delegates execution via _run_async_impl.
    """
    model_config = {"arbitrary_types_allowed": True}
    
    assistant: LlmAgent = Field(description="The internal conversational LLM agent")

    def __init__(self):
        assistant_agent = LlmAgent(
            name=AGENT_NAME,
            model=AGENT_MODEL,
            description=AGENT_DESCRIPTION,
            planner=BuiltInPlanner(
                thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
            ),
            instruction=CAREFLOW_SYSTEM_PROMPT,
            # PASSING ALL TOOLS: A2A + MCP (Database) + Retry + Interaction Logger + Clinical Tools + Schedule Tools
            tools=a2a_tools + mcp__tool_loader.all_tools + retry_tools + interaction_tools + clinical_tools + schedule_tools,
            output_key="patient_monitoring"
        )
        
        super().__init__(
            name=AGENT_NAME,
            assistant=assistant_agent,
            sub_agents=[assistant_agent]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Core execution logic. Delegates to the internal LlmAgent.
        """
        async for event in self.assistant.run_async(ctx):
            yield event

    async def process_message(self, message: Message, context: RequestContext):
        pass

# Create the singleton agent instance
root_agent = CareFlowAgent()
