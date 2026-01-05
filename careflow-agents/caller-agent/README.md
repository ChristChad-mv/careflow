# CareFlow Pulse Caller Agent

The voice interface agent that integrates with Twilio and communicates with the CareFlow Pulse Agent.

## Project Structure

This project is organized as follows:

```
caller-agent/
├── app/                 # Core application code
│   ├── agent.py         # LangGraph agent with Twilio integration
│   ├── server.py        # FastAPI server (A2A + WebSocket + TwiML)
│   ├── executor/        # A2A protocol executor implementation
│   ├── prompts/         # System prompts for the agent
│   └── app_utils/       # App utilities and helpers
│       ├── config.py    # Configuration management
│       └── llm.py       # LLM model setup
├── .cloudbuild/         # CI/CD pipeline configurations for Google Cloud Build
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
├── GEMINI.md            # AI-assisted development guide
└── pyproject.toml       # Project dependencies and configuration
```

## Setup

Ensure you have completed the [root setup](../README.md) (venv activation, dependencies, toolbox).

## Running as a Server (Voice + A2A)

To run the full server (handles Twilio Voice calls AND A2A requests):

1.  Navigate to this directory:
    ```bash
    cd careflow-agent/careflow-pulse-caller
    ```

2.  Run the server:
    ```bash
    uv run python app/server.py
    ```
    The server will start on port **8000** (configured in `.env`).

    *   **Twilio Webhook**: Configure your Twilio number to point to `https://<your-url>/twiml`.
    *   **A2A Endpoint**: The agent is discoverable at `http://localhost:8000/.well-known/agent.json`.

## Running as a Client (Chat Console)

To test the agent logic in the terminal without making a phone call:

1.  Navigate to this directory:
    ```bash
    cd careflow-agent/careflow-pulse-caller
    ```

2.  Run the chat console:
    ```bash
    PYTHONPATH=. python3 chat_console.py
    ```
    You can now chat with the agent. It will simulate the voice conversation flow.
