# CareFlow Pulse Agents

This directory contains the two main agents for the CareFlow Pulse system:

1.  **CareFlow Pulse Agent** (`careflow-agent/`): The core logic agent that monitors patient data and generates alerts.
2.  **CareFlow Pulse Caller** (`caller-caller/`): The voice interface agent that handles phone calls (via Twilio) and communicates with the core agent.

## Prerequisites

Before running any agent, you must start the **MCP Toolbox**.

1.  Navigate to the mcp folder.
2.  Run the toolbox:
    ```bash
    ./toolbox --tools-file careflow-agent/mcp/tools.yaml
    ```
    Keep this terminal open.

3.  **Environment Variables**:
    - Ensure you have a `.env` file in `careflow-agent/` with the necessary keys (`GOOGLE_API_KEY`, `TWILIO_...`, etc.).
    - This file is automatically loaded by the agents.

## Running the Agents

Please refer to the specific READMEs for detailed instructions:

- [CareFlow Pulse Agent README](./careflow_pulse_agent/README.md)
- [CareFlow Pulse Caller README](./careflow_pulse_caller/README.md)
