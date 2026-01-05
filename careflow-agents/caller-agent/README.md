# CareFlow Pulse Caller Agent

Voice interface agent powered by **Gemini 2.0 Flash** for ultra-low latency conversations. Handles patient phone calls via Twilio ConversationRelay and communicates with CareFlow Pulse Agent using A2A protocol.

## ✨ Features

- 🎤 **Voice Conversations**: Real-time voice interactions with patients via Twilio
- ⚡ **Low Latency**: Gemini 2.0 Flash optimized for sub-second response times
- 🔄 **A2A Protocol**: Seamless communication with CareFlow Pulse medical agent
- 🌐 **WebSocket Streaming**: Real-time bidirectional audio streaming
- 🎯 **Task Delegation**: Automatically delegates medical queries to specialist agent
- 📞 **Dual Mode**: Handles both inbound (patient calls) and outbound (system calls patient)

## 🏗️ Architecture

```
caller-agent/
├── app/                          # Core application code
│   ├── agent.py                  # LangGraph ReAct agent (Gemini 2.0 Flash)
│   ├── server.py                 # FastAPI server (A2A + WebSocket + TwiML)
│   ├── config.yaml               # Agent configuration
│   └── app_utils/                # Utilities and helpers
│       ├── config.py             # Environment configuration
│       ├── llm.py                # Gemini 2.0 model setup
│       ├── conversation_relay.py # Twilio ConversationRelay integration
│       ├── telemetry.py          # OpenTelemetry instrumentation
│       ├── executor/
│       │   └── caller_executor.py # A2A protocol executor
│       └── prompts/
│           └── system_prompts.py  # System prompts & instructions
├── deployment/                    # Terraform infrastructure
├── tests/                         # Unit, integration, load tests
├── Makefile                       # Development commands
└── pyproject.toml                 # Dependencies (uv)
```

## 🚀 Technology Stack

- **LLM**: Gemini 2.0 Flash (optimized for voice, low-latency)
- **Framework**: LangGraph (ReAct agent pattern)
- **Server**: FastAPI + uvicorn
- **Voice**: Twilio ConversationRelay + ElevenLabs TTS
- **Protocol**: A2A (Agent-to-Agent communication)
- **Package Manager**: uv (fast Python dependency management)
- **Observability**: OpenTelemetry + Google Cloud Logging

## 📋 Prerequisites

- **Python 3.10-3.13**
- **uv** package manager ([installation](https://docs.astral.sh/uv/getting-started/installation/))
- **Google Cloud Project** with Vertex AI API enabled
- **Twilio Account** with phone number configured
- **ElevenLabs Account** (for TTS)
- **Ngrok** (for local development with Twilio webhooks)

## 🔧 Setup

### 1. Install Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
make install
# or: uv sync
```

### 2. Configure Environment Variables

Copy and configure your `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Google AI Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_API_KEY=your-api-key

# Server Configuration
PORT=8000

# A2A Configuration - CareFlow Pulse Agent URL
CAREFLOW_AGENT_URL=http://localhost:8001

# Twilio Configuration
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Local Development (Ngrok)
NGROK_URL=your-ngrok-url.ngrok-free.app
```

### 3. Configure Twilio Webhook

1. Start ngrok: `ngrok http 8000`
2. Copy the ngrok URL (e.g., `https://abc123.ngrok-free.app`)
3. Update `NGROK_URL` in `.env`
4. In Twilio Console, set webhook URL: `https://your-ngrok-url/twiml`

## 🎯 Running the Server

### Development Mode (with hot-reload)

```bash
make local-backend
```

Or manually:
```bash
uv run uvicorn app.server:app --host localhost --port 8000 --reload
```

### Production Mode

```bash
uv run python app/server.py
```

The server will start on **http://localhost:8000** with:
- 📞 TwiML endpoint: `http://localhost:8000/twiml`
- 🔌 WebSocket endpoint: `ws://localhost:8000/ws`
- 🤖 A2A endpoint: `http://localhost:8000/.well-known/agent-card.json`

## 🧪 Development Commands

```bash
# Install dependencies
make install

# Run development server
make local-backend

# Run with A2A inspector
make playground

# Lint code
make lint

# Run tests
make test
```

## 🔍 A2A Protocol Testing

Launch the A2A inspector to test agent interactions:

```bash
make inspector
```

Inspector UI will be available at: **http://localhost:5001**

Test locally by entering: `http://localhost:8000/.well-known/agent-card.json`

## 🚢 Deployment

Deploy to Google Cloud Run:

```bash
make deploy
```

This will:
1. Build Docker container
2. Push to Artifact Registry
3. Deploy to Cloud Run
4. Configure IAM and networking

## 📊 Monitoring

The agent includes OpenTelemetry instrumentation with traces exported to:
- Google Cloud Trace
- Custom OTLP endpoint (configurable)

Logs are sent to Google Cloud Logging for centralized monitoring.

## 🎨 Code Quality

The codebase follows:
- **Type hints**: Full mypy type checking
- **Linting**: Ruff for fast Python linting
- **Formatting**: Ruff formatter (Black-compatible)
- **Documentation**: Comprehensive docstrings

## 📝 Key Components

### Agent (`agent.py`)
- LangGraph ReAct agent with Gemini 2.0 Flash
- Tools: `call_patient`, `list_remote_agents`, `send_remote_agent_task`
- Conversation memory with MemorySaver
- Call deduplication to prevent duplicate outbound calls

### Server (`server.py`)
- FastAPI application with WebSocket support
- TwiML endpoint for Twilio webhooks
- A2A protocol mounted at root
- OpenTelemetry instrumentation

### Executor (`app_utils/executor/caller_executor.py`)
- Implements A2A `AgentExecutor` interface
- Manages task lifecycle (submitted → working → completed)
- Streams responses via EventQueue

### Prompts (`app_utils/prompts/system_prompts.py`)
- Dual-mode instructions (inbound/outbound calls)
- Interview flow for wellness checks
- Retry policies and error handling

## 🤝 Integration with CareFlow Pulse Agent

The Caller Agent delegates medical queries to the CareFlow Pulse Agent via A2A protocol:

1. Patient mentions symptoms during call
2. Caller Agent uses `send_remote_agent_task` to query medical agent
3. Medical agent analyzes symptoms and returns recommendations
4. Caller Agent relays information back to patient via voice

## 📚 Additional Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Gemini 2.0 API](https://ai.google.dev/gemini-api/docs)
- [Twilio ConversationRelay](https://www.twilio.com/docs/voice/twiml/stream)
- [A2A Protocol Specification](https://github.com/a2aproject)
    You can now chat with the agent. It will simulate the voice conversation flow.
