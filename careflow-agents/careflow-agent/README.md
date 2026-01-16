# CareFlow Pulse Agent

> **Medical Intelligence Orchestrator powered by Gemini 3 Pro**

The **CareFlow Pulse Agent** is the analytical brain of the platform. Built with the Google Agent Development Kit (ADK), it orchestrates patient monitoring, performs advanced clinical reasoning, and manages database operations via the Model Context Protocol (MCP).

## ✨ Key Capabilities

- **🧠 Advanced Medical Reasoning**: Leveraging **Gemini 3 Pro** to analyze complex clinical data, identify risk factors, and generate evidence-based recommendations.
- **🎙️ Audio-First Analysis**: Fetches raw call recordings from Twilio and uses Gemini 3's **native multimodal capabilities** to analyze tone, sentiment, and distress signals directly from audio.
- **🔄 A2A Orchestration**: Coordinates with the **Caller Agent** via the Agent-to-Agent (A2A) protocol. It delegates patient interview tasks ("outbound rounds") and handles inbound queries.
- **🏥 Hospital-Scoped Security**: Enforces strict data isolation by `hospitalId`.
- **🔌 MCP Integration**: Uses the **Model Context Protocol Toolbox for Databases** to interact safely with the Firestore database (CRUD operations, logging, alerts).

## 🏗️ Architecture

The agent is built using a **BaseAgent wrapper pattern** for fine-grained control over execution and tool callbacks.

```
careflow-agent/
├── app/
│   ├── agent.py                  # CareFlowAgent class & Gemini 3 config
│   ├── server.py                 # FastAPI server (A2A Protocol endpoints)
│   ├── tools/
│   │   ├── mcp__tool_loader.py   # Loads tools from MCP Toolbox
│   │   ├── a2a_tools.py          # Tools to talk to Caller Agent
│   │   └── twilio_audio.py       # Tool to fetch audio for multimodal analysis
│   ├── callbacks/
│   │   └── multimodal_handoff.py # Injects audio into LLM context
│   └── app_utils/                # Config, Prompts, Telemetry
├── deployment/                   # Terraform infrastructure
├── tests/                        # Unit, evals and integration tests
└── Makefile                      # Dev commands
```

## 🚀 5 Core Workflows

The agent implements 5 distinct workflows to handle different triggers:

1. **Trigger Rounds**: Starts daily check-ins -> Delegates to Caller Agent.
2. **Audio-First Analysis**: Receives "Call Complete" -> Fetches Audio -> Analyzes Risk -> Updates DB.
3. **Text Summary Processing**: Fallback analysis of text transcripts.
4. **Answer Questions**: Responds to clinical questions from the Caller Agent.
5. **Inbound Call Support**: identifies patients calling in.

## 🛠️ Technology Stack

- **Model**: Gemini 3 Pro (Preview)
- **Framework**: Google ADK 1.6+ (Python)
- **Protocols**: A2A (JSON-RPC), MCP (Toolbox)
- **Database**: Firestore (via MCP)
- **Observability**: OpenTelemetry + Cloud Logging

## 🔧 Getting Started

### Prerequisites

- Python 3.10+
- `uv` package manager
- Google Cloud Credentials (Application Default)

### Installation

```bash
make install
```

### Running Locally

To start the agent server (typically on port **8080**):

```bash
make local-backend
```

- **Agent Endpoint**: `http://localhost:8080`
- **Agent Card**: `http://localhost:8080/.well-known/agent.json`

### Environment Variables

Create a `.env` file:

```env
PORT=8080
GOOGLE_CLOUD_PROJECT=careflow-478811
MODEL=gemini-3-flash-preview
CAREFLOW_CALLER_URL=http://localhost:8080
MCP_TOOLBOX_URL=http://localhost:5000
```

## 🧪 Testing

Run unit and integration tests:

```bash
make test
```

Launch the A2A Inspector to debug agent interactions:

```bash
make inspector
```

## 🚢 Deployment

Deploy to Google Cloud Run:

```bash
make deploy
```
