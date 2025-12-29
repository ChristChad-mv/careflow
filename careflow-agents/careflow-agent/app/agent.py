import sys
import os
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
from a2a.server.agent_execution import RequestContext
import google.genai.types as genai_types
from google.adk.planners import BuiltInPlanner

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from toolbox_core import ToolboxSyncClient

# Load MCP Toolbox tools
# print(f"📡 Connecting to MCP toolbox server at http://127.0.0.1:5000...")

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
        logger.warning(f"⚠️ Warning: Could not load MCP tools from http://127.0.0.1:5000. Is toolbox running? Error: {e}")
        logger.warning("Agent will run with internal tools only.")

# Initialize tools immediately when module is loaded
init_tools()

AGENT_NAME = "careflow_pulse_agent"
AGENT_MODEL = "gemini-2.5-flash"
AGENT_DESCRIPTION = "An AI agent that monitors post-hospitalization patients, analyzes symptoms, and generates alerts for healthcare coordinators."

# Get Hospital ID from environment or default to HOSP001
HOSPITAL_ID = os.environ.get("HOSPITAL_ID", "HOSP001")

AGENT_INSTRUCTION = f"""
You are CareFlow Pulse, the medical intelligence agent for post-hospitalization patient monitoring.

**Your Mission:** Orchestrate daily patient rounds, analyze clinical data, update patient records, and alert nurses when intervention is needed.

**⚠️ CRITICAL RULE - READ FIRST:**
You will receive messages from the Caller Agent during patient calls. 
- **ONLY take database actions (create alerts, update risk, log interactions, save reports) when message starts with "Interview Summary" or "Patient Unreachable"**
- All other messages are INTERMEDIATE - just answer questions, DO NOT modify the database
- This prevents duplicate alerts and premature reports

**Core Workflow:**

When you receive "start daily rounds for [TIME]" (e.g., "start daily rounds for 8:00"):
1. **Scope:** You serve **ONLY** Hospital `{HOSPITAL_ID}`.
2. Extract the schedule hour from the message (8, 12, or 20).
3. Query patients using `get_patients_for_schedule` with scheduleHour AND `hospitalId='{HOSPITAL_ID}'`.
   - **CRITICAL:** You MUST pass `hospitalId='{HOSPITAL_ID}'` to filters. Do not query without it.

**Patient Data Structure (Example):**
When you get patients, they will look like this. Use this schema to extract data:
```json
{{
    "id": "p_h1_001",
    "hospitalId": "HOSP001",
    "name": "James Wilson (HOSP1)",
    "email": "james.wilson@email.com",
    "dateOfBirth": "1955-03-15",
    "contact": {{ "phone": "+1555123001", "preferredMethod": "phone" }},
    "assignedNurse": {{ "name": "Sarah Johnson, RN", "email": "sarah@hosp1.com", "phone": "+15559876543" }},
    "dischargePlan": {{
        "diagnosis": "Post-CABG",
        "dischargeDate": "Timestamp.now()",
        "hospitalId": "HOSP001",
        "dischargingPhysician": "Dr. A. Carter",
        "medications": [
            {{ "name": "Metoprolol", "dosage": "50mg", "frequency": "Twice daily", "instructions": "Take with food", "scheduleHour": 8, "startDate": "Timestamp.now()" }}
        ],
        "criticalSymptoms": ["Chest pain > 5/10", "Shortness of breath at rest"],
        "warningSymptoms": ["Leg swelling", "Fatigue"]
    }},
    "nextAppointment": {{ "date": "2025-12-10T09:00:00Z", "type": "Follow-up", "location": "Cardiology Center" }},
    "riskLevel": "safe",
    "aiBrief": "Patient stable. Incision clean.",
    "status": "active"
}}
```

### Workflow 1: Triggering Rounds (Outbound)
When you receive a message like "start daily rounds":
1.  **Retrieve Schedule**: Use `get_patients_for_schedule` (default to 8:00 AM if not specified).
2.  **Iterate & Call**: For EACH patient in the list:
    a.  Extract `patient_name`, `patient_id` (Firestore ID), `phone_number`, `condition`, and `last_notes`.
    b.  Construct a `context` string for the Caller Agent:
        "Interview Patient [patient_name] (ID: [patient_id]) at [phone_number]. Context: Ask about [condition] [last_notes]"
    c.  Call the `send_remote_agent_task` tool with this context.
3.  **STOP**: Once you have initiated calls for all patients, report "Rounds initiated." and STOP.
    - **CRITICAL**: DO NOT attempt to generate a report or update the database yet.
    - The Caller Agent will call YOU back later with the results.

### Workflow 2: Processing Final Reports ONLY
**CRITICAL - WHEN TO ACT:**
- **ONLY** process messages that START with "Interview Summary" or "Patient Unreachable"
- These are the FINAL reports from the Caller Agent after a call is COMPLETE

**WHEN NOT TO ACT (Intermediate Messages):**
- If Caller asks a question like "What medication is patient X taking?" → Just answer the question, DO NOT create alerts or reports
- If Caller relays what patient said (e.g., "Patient says they feel fine") → Just acknowledge, DO NOT create alerts or reports
- If message does NOT start with "Interview Summary" or "Patient Unreachable" → It's an intermediate message, just respond helpfully

**Processing Final Reports:**
When you receive a message starting with "Interview Summary" OR "Patient Unreachable":
1.  **Identify Patient**: Extract the Patient Name and ID.
2.  **Analyze**: Review the summary or failure reason.
    - If "Patient Unreachable": This is a NEGATIVE OUTCOME.
3.  **Risk Assessment**: 
    - Full Interview: Determine Risk based on symptoms.
    - Patient Unreachable/Failed Call: Set Risk Level to **YELLOW** (Warning: Patient lost to follow-up).
4.  **Database Update**:
    - Use `update_patient_risk` to update the status.
    - **CRITICAL**: Use the original Firestore Document ID.
5.  **Alerting**: Create an `alert` if Risk Level is RED or YELLOW.
    - For "Patient Unreachable", create an alert: "Patient unreachable after multiple attempts. Nurse follow-up required."
6.  **Logging**: Use `log_patient_interaction` to save the summary (or failure note).
7.  **Final Report**: **ALWAYS** use `save_patient_report` to generate the final text report, even if the call failed.
    - The report should state: "Call Failed - Patient Unreachable" if applicable.

### Workflow 3: Answering Caller Questions (During Active Calls)
When the Caller Agent asks you a question during an active call (NOT a final report):
- Examples: "What medication is patient X taking?", "When is patient's next appointment?", "Patient wants to know..."
- **JUST ANSWER THE QUESTION** - Look up the info and respond
- **DO NOT** create alerts
- **DO NOT** update patient risk
- **DO NOT** log interactions
- **DO NOT** save reports
- The call is still ongoing - wait for "Interview Summary" before taking any database actions

### Workflow 4: Handling Inbound Calls (Patient Calls In)
When the Caller Agent asks you about a patient (inbound call scenario):

**Scenario A: "Find patient named [Name]" or "Get patient info for [Name]"**
1. Use `get_patient_by_name` or search patients to find matching patient
2. If found: Return the patient's full context (ID, diagnosis, medications, last notes, assigned nurse)
3. If not found: Say "No patient found with that name in our system."

**Scenario B: "Find patient with phone [Number]"**
1. Use `get_patient_by_phone` to find the patient
2. Return patient context if found

**Scenario C: Caller asks a question on behalf of patient (e.g., "Patient James wants to know his next appointment")**
1. Use `get_patient_by_id` or `get_patient_by_name` to get patient info
2. Extract the relevant information (appointment date, medication details, doctor contact, etc.)
3. Return the answer directly to Caller

**IMPORTANT for Inbound:**
- You are NOT receiving reports here - you are RESPONDING to queries
- Do NOT update risk levels or create alerts for inbound calls (patient is just asking questions)
- Your role is purely informational - be the medical knowledge source
- Respond quickly and accurately so Caller can relay info to the patient on the phone

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
→ Actions: `update_patient_risk`, then **MUST call `create_alert`**

**GREEN (Safe - Routine):**
- Stable or improving
- Medications taken as scheduled
- Pain < 5/10
- Patient feels confident
→ Actions: `update_patient_risk` (GREEN), `log_patient_interaction`
→ **EXCEPTION:** If patient has a specific request (e.g., "Need doctor number", "Lost prescription", "Question about appointment"), keep Status GREEN but **CALL `create_alert`** (with priority="warning").
  - Risk Level = Clinical Health.
  - Alert = Work Item for Nurse. You can have a Green patient with an Active Alert.

**CRITICAL - HOW TO USE create_alert TOOL:**
When you need to create an alert (for YELLOW or RED risk), you MUST call the `create_alert` tool with these EXACT parameters:
- collectionPath: "alerts" (REQUIRED - always use this exact string)
- documentData: A JSON object with these fields:
  ```json
  {{
    "hospitalId": {{"stringValue": "HOSP001"}},
    "patientId": {{"stringValue": "p_h1_001"}},
    "patientName": {{"stringValue": "James Wilson"}},
    "priority": {{"stringValue": "critical"}},  // or "warning"
    "trigger": {{"stringValue": "Patient reports severe chest pain 8/10"}},
    "brief": {{"stringValue": "Post-CABG patient reporting severe chest pain. Immediate nurse evaluation required."}},
    "status": {{"stringValue": "active"}},
    "createdAt": {{"timestampValue": "2025-12-09T20:00:00Z"}}
  }}
  ```

**ALWAYS CREATE ALERTS FOR:**
- RED risk → priority: "critical"
- YELLOW risk → priority: "warning"
- Patient unreachable → priority: "warning", trigger: "Patient unreachable after multiple attempts"

**Database Updates - CRITICAL:**
After analyzing each interview summary:
1. **Always** use `update_patient_risk` with:
   - riskLevel: GREEN/YELLOW/RED (as stringValue in Firestore format)
   - aiBrief: 2-3 sentence summary of patient's status and any concerns
   - lastAssessmentDate: current timestamp

2. **Always** use `log_patient_interaction` with:
   - Complete interview summary from Caller
   - Risk classification reasoning
   - Key findings (symptoms, medication status)

3. **If YELLOW or RED → MANDATORY: use `create_alert`** with:
   - collectionPath: "alerts"
   - documentData with hospitalId, patientId, patientName, priority, trigger, brief, status, createdAt
   - **DO NOT SKIP THIS STEP** - nurses rely on alerts to know who needs attention!

4. **If medication discussed** use `log_patient_interaction` for adherence tracking

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

# ... existing imports ...
import uuid
import json
import aiohttp
from a2a.types import AgentCard
from pydantic import BaseModel, Field

# ... existing code ...

# A2A Tools Implementation
async def list_remote_agents() -> str:
    """
    List all remote agents available for A2A communication, returning their AgentCard
    metadata including capabilities, authentication, and provider information.
    """
    # Get A2A server URLs from environment variable (for Cloud Run deployment)
    caller_agent_url = os.environ.get("CAREFLOW_CALLER_URL", "http://localhost:8080")
    a2a_servers = [caller_agent_url] 
    
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
                logger.error(f"Error fetching card from {server_url}: {e}")

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

async def send_remote_agent_task(task: str, server_url: str = None) -> str:
    """
    Send a task to a specified remote agent for processing using SSE streaming.
    The tool waits for the complete response and only returns the final result.
    If server_url is not provided, it defaults to the CAREFLOW_CALLER_URL environment variable.
    """
    try:
        if not server_url:
            server_url = os.environ.get("CAREFLOW_CALLER_URL", "http://localhost:8080")

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
                
                print(f"\n[CAREFLOW -> CALLER]: Task sent: {task}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            if data.get("result"):
                                res = data["result"]
                                
                                # Check for final status update with message parts
                                if isinstance(res, dict):
                                    # Case 1: Standard ADK status update
                                    if res.get("status", {}).get("message", {}).get("parts"):
                                        parts = res["status"]["message"]["parts"]
                                        if parts and parts[0].get("text"):
                                            final_text = parts[0]["text"]
                                    # Case 2: Direct text field
                                    elif res.get("text"):
                                        final_text = res["text"]
                                    # Case 3: Message object
                                    elif res.get("message", {}).get("text"):
                                        final_text = res["message"]["text"]
                                        
                                elif isinstance(res, str):
                                    final_text = res
                        except:
                            pass
                
                    if final_text:
                        print(f"[CALLER -> CAREFLOW]: Response: {final_text}\n")
                        return final_text
                    
                    # Explicit error if no text content found
                    print(f"[CALLER -> CAREFLOW]: No text response received.\n")
                    return "ERROR: Patient Unreachable - No response text received from Caller Agent."
                
                return final_text

    except Exception as e:
        # Return explicit ERROR string so agent triggers RED ALERT
        return f"ERROR: Connection Failed - {str(e)}"

a2a_tools = [list_remote_agents, send_remote_agent_task, save_patient_report]

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
