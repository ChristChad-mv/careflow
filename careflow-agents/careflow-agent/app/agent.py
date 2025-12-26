import sys
import os
import uuid
import json
import aiohttp
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from typing import AsyncGenerator
from pydantic import Field
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from a2a.types import Message
from a2a.types import AgentCard
from a2a.server.agent_execution import RequestContext
import google.genai.types as genai_types
from google.adk.planners import BuiltInPlanner


from toolbox_core import ToolboxSyncClient

# Load MCP Toolbox tools
print(f"📡 Connecting to MCP toolbox server at http://127.0.0.1:5000...")

# Keep client open globally so tools can use it
toolbox_client = None
all_tools = []

def init_tools():
    global toolbox_client, all_tools
    try:
        # Don't use 'with' - we need to keep the session open
        toolbox_client = ToolboxSyncClient("http://127.0.0.1:5000")
        # Load our custom toolset
        all_tools = toolbox_client.load_toolset("patient_tools")
        print(f"Total tools available: {len(all_tools)} MCP tools")
    except Exception as e:
        print(f"⚠️ Warning: Could not load MCP tools: {e}")
        # import traceback
        # traceback.print_exc()

# Initialize tools immediately when module is loaded
init_tools()

AGENT_NAME = "careflow_pulse_agent"
AGENT_MODEL = "gemini-2.5-flash"
AGENT_DESCRIPTION = "An AI agent that monitors post-hospitalization patients, analyzes symptoms, and generates alerts for healthcare coordinators."

AGENT_INSTRUCTION = f"""
    You are CareFlow Pulse, an AI-powered post-hospitalization patient monitoring agent.
    Your primary mission is to help nurse coordinators monitor recently discharged patients
    and prevent readmissions through proactive care and early intervention.

    **Your Core Responsibilities:**
    
    1. **Patient Monitoring**
       - Track patient check-ins and symptom reports
       - Monitor medication adherence
       - Analyze vital signs trends
       - Identify concerning patterns or deterioration
    
    2. **Symptom Analysis**
       - Assess symptom severity and urgency
       - Identify warning signs of complications
       - Recognize patterns that indicate worsening condition
       - Consider patient history and diagnosis context
    
    3. **Alert Generation**
       - Generate critical alerts for immediate attention
       - Create warning alerts for potential concerns
       - Provide safe status updates for stable patients
       - Include actionable recommendations for nurse coordinators
    
    4. **Risk Assessment**
       - Calculate readmission risk scores
       - Identify high-risk patients requiring closer monitoring
       - Consider social determinants of health
       - Flag medication non-adherence or missed check-ins
    
    5. **Communication Support**
       - Help draft clear, empathetic patient communications
       - Suggest follow-up questions for patient check-ins
       - Provide health education content
       - Assist with care coordination

    **Patient Monitoring Guidelines:**
    
    - **Critical Severity (Immediate Action Required):**
      * Severe symptoms: chest pain, difficulty breathing, confusion
      * Vital signs outside safe ranges
      * Sudden deterioration or significant changes
      * Medication adverse reactions
      → Generate CRITICAL alert with immediate action plan
    
    - **Warning Severity (Close Monitoring Needed):**
      * Moderate symptoms: increased pain, swelling, fatigue
      * Vital signs trending unfavorably
      * Missed medications or check-ins
      * Multiple minor concerns accumulating
      → Generate WARNING alert with monitoring recommendations
    
    - **Safe Status (Routine Monitoring):**
      * Stable or improving symptoms
      * Good medication adherence
      * Regular check-ins completed
      → Generate SAFE status update
      
    **Response Format:**
    Always start your response with the patient's current status (CRITICAL, WARNING, or SAFE) if you have enough information.
    Be concise and action-oriented.
    ## Alert Recommendation
    - **Severity**: [Safe/Warning/Critical]
    - **Priority**: [Routine/Elevated/Urgent]
    - **Recommended Action**: [Specific next steps for nurse coordinator]
    
    ## Next Steps
    [Clear action items for follow-up]

    **Clinical Context:**
    - You have access to patient diagnosis, medications, and medical history
    - Consider patient's age, comorbidities, and social situation
    - Follow evidence-based clinical guidelines
    - Always err on the side of caution - escalate when uncertain
    
    **Communication Style:**
    - Professional but compassionate
    - Clear and actionable language for healthcare providers
    - Evidence-based recommendations
    - Culturally sensitive and patient-centered
    
    **Current Context:**
    - Current date: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    - You have thinking capabilities enabled - use them to analyze complex cases
    - Consider both clinical and social factors in your assessments
    - Prioritize patient safety above all else

    Remember: Your goal is to prevent readmissions through early detection and proactive intervention.
    Every alert you generate could save a life or prevent unnecessary suffering.
    """


# A2A Tools Implementation
async def list_remote_agents() -> str:
    """
    List all remote agents available for A2A communication, returning their AgentCard
    metadata including capabilities, authentication, and provider information.
    """
    # Hardcoded list of servers for now, or load from config
    a2a_servers = ["http://localhost:8080"] 
    
    agent_cards = []
    async with aiohttp.ClientSession() as session:
        for server_url in a2a_servers:
            try:
                agent_card_url = f"{server_url}/.well-known/agent.json"
                async with session.get(agent_card_url, headers={"Accept": "application/json"}) as response:
                    if response.ok:
                        card_data = await response.json()
                        agent_cards.append(AgentCard.model_validate(card_data))
            except Exception as e:
                print(f"Error fetching card from {server_url}: {e}")

    if not agent_cards:
        return "No remote A2A servers are currently available."

    formatted_cards = []
    for i, card in enumerate(agent_cards):
        formatted_cards.append(f"{i+1}. {card.name} ({card.url}) - {card.description}")
    
    return "Available remote agents:\n" + "\n".join(formatted_cards)

async def send_remote_agent_task(server_url: str, task: str) -> str:
    """
    Send a task to a specified remote agent for processing using SSE streaming.
    The tool waits for the complete response and only returns the final result.
    Requires server_url and task parameters.
    """
    try:
        # Generate IDs
        request_id = int(uuid.uuid1().int >> 64)
        task_id = f"task_{int(uuid.uuid1().int >> 64)}_{uuid.uuid4().hex[:9]}"

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "id": request_id,
            "params": {
                "message": {
                    "messageId": task_id,
                    "kind": "message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": task}]
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                server_url,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                json=rpc_request
            ) as response:
                if not response.ok:
                    return f"Error: HTTP {response.status} {response.reason}"

                # Simple SSE processing to get final text
                final_text = ""
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            if data.get("result"):
                                # Extract text from result
                                res = data["result"]
                                if isinstance(res, dict):
                                    if res.get("message", {}).get("text"):
                                        final_text = res["message"]["text"]
                                    elif res.get("text"):
                                        final_text = res["text"]
                                elif isinstance(res, str):
                                    final_text = res
                        except:
                            pass
                
                return final_text or "Task completed but no text response received."

    except Exception as e:
        return f"Error sending task: {str(e)}"

a2a_tools = [list_remote_agents, send_remote_agent_task]

class CareFlowAgent(BaseAgent):
    """
    Custom CareFlow Agent following the user's VoiceAgent pattern.
    Wraps an internal LlmAgent and delegates execution via _run_async_impl.
    """
    model_config = {"arbitrary_types_allowed": True}
    
    assistant: LlmAgent = Field(description="The internal conversational LLM agent")

    def __init__(self):
        # 1. Create internal LlmAgent
        assistant_agent = LlmAgent(
            name=AGENT_NAME,
            model=AGENT_MODEL,
            description=AGENT_DESCRIPTION,
            planner=BuiltInPlanner(
                thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
            ),
            instruction=AGENT_INSTRUCTION,
            tools=all_tools + a2a_tools, # Add A2A tools here
            output_key="patient_monitoring",
        )
        
        # 2. Initialize BaseAgent
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

# Create the agent instance
root_agent = CareFlowAgent()
