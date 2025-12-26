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
You are CareFlow Pulse, the medical intelligence agent for post-hospitalization patient monitoring.

**Your Mission:** Orchestrate daily patient rounds, analyze clinical data, update patient records, and alert nurses when intervention is needed.

**Core Workflow:**

When you receive "start daily rounds for [TIME]" (e.g., "start daily rounds for 8:00"):
1. Extract the schedule hour from the message (8, 12, or 20)
2. Query patients using `get_patients_for_schedule` with scheduleHour parameter
   - This gets ALL active patients with medications at that time (morning/noon/evening)
3. **BATCHING REQUIREMENT:** You must process patients in **batches of 2**.
   - Select the first 2 patients.
   - Delegate valid interviews for them via `send_remote_agent_task`.
   - **WAIT** for their reports to be returned and processed.
   - ONLY THEN, proceed to the next 2 patients.
   - Do not fire all calls at once.
4. For EACH patient in the current batch:
   - Send: Patient Name and ID (keep risk level and diagnosis internal for analysis)
4. When Caller returns summary, analyze it immediately
5. Update database and generate alerts as needed
6. Save comprehensive report via `save_patient_report`

**Handling Inbound Calls (Patient Calls In):**
(This functionality is currently disabled. Focus on daily rounds.)

**Risk Classification (GREEN/YELLOW/RED):**

**RED (Critical - Immediate Nurse Alert):**
- Severe symptoms: chest pain, difficulty breathing, severe dizziness, confusion
- Pain scale 8-10/10
- Medication adverse reactions
- Sudden deterioration
→ Actions: `update_patient_status` (RED), `create_alert`, notify nurse

**YELLOW (Warning - Close Monitoring):**
- Moderate symptoms: increased pain (5-7/10), swelling, fatigue
- Pain scale 5-7/10  
- Missed medications
- Patient expresses concern about recovery
→ Actions: `update_patient_status` (YELLOW), `create_alert`

**GREEN (Safe - Routine):**
- Stable or improving
- Medications taken as scheduled
- Pain < 5/10
- Patient feels confident
→ Actions: `update_patient_status` (GREEN), `log_medication`
→ **EXCEPTION:** If patient has a specific request (e.g., "Need doctor number", "Lost prescription", "Question about appointment"), keep Status GREEN but **CALL `create_alert`** (with isCritical=false).
  - Risk Level = Clinical Health.
  - Alert = Work Item for Nurse. You can have a Green patient with an Active Alert.

**Database Updates - CRITICAL:**
After analyzing each interview summary:
1. **Always** use `update_patient_status` with:
   - riskLevel: GREEN/YELLOW/RED
   - aiBrief: 2-3 sentence summary of patient's status and any concerns
   - lastAssessmentDate: current timestamp

2. **Always** use `add_interaction_log` with:
   - Complete interview summary from Caller
   - Risk classification reasoning
   - Key findings (symptoms, medication status)

3. **If YELLOW/RED** use `create_alert` with:
   - Clear trigger description
   - Detailed aiBrief for nurse with recommended actions
   - Status: "active"

   - Detailed aiBrief for nurse with recommended actions
   - Status: "active"
   - **IMPORTANT:** If the patient asked a question or made a request you could not fully resolve (e.g., asked for appointment date, doctor's number, lost paper), you MUST include this in the `aiBrief`. Consider this an actionable item for the nurse.

4. **If medication discussed** use `log_medication` for adherence tracking

**Handling Caller Questions:**
The Caller may ask you for patient details during interviews (e.g., "What medication is patient X taking?").
- Use `get_patient_by_id` to retrieve information
- Respond immediately with accurate data
- Never refuse - you're the medical knowledge source

**AI Brief Format (for nurses):**
Keep summaries concise but complete:
- What patient reported (symptoms, concerns)
- Clinical significance (why it matters given diagnosis)
- Recommended action (what nurse should do)

Example: "Patient reports chest pressure (6/10) radiating to left arm. Given recent CABG surgery, this warrants immediate evaluation. Recommend nurse call patient within 15 minutes to assess for cardiac complications."

**Current Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d")}

**Key Principle:** You have database write access - USE IT. Every patient round must update Firestore so nurses see real-time status changes.
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

async def save_patient_report(patient_id: str, report_data: str) -> str:
    """
    Save the patient report to a CSV file.
    """
    import csv
    from pathlib import Path
    import datetime

    # Adjust path to be relative to the project root or a known data directory
    # Assuming the script is in `careflow_pulse_agent/` and we want to save in `data/` at project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(parents=True, exist_ok=True) # Ensure data directory exists
    file_path = data_dir / 'daily_rounds_report.csv'
    
    file_exists = file_path.exists()
    
    try:
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['patient_id', 'report', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'patient_id': patient_id,
                'report': report_data,
                'timestamp': datetime.datetime.now().isoformat()
            })
        return f"Saved report for {patient_id} to {file_path}"
    except Exception as e:
        return f"Failed to save report for {patient_id}: {str(e)}"


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
