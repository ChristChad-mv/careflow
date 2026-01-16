# CareFlow Caller Agent

> **Voice Interface powered by Gemini 2.0 Flash (Low-Latency)**

The **CareFlow Caller Agent** handles all real-time voice interactions with patients. Optimized for sub-second latency, it conducts fluid, natural phone conversations using Twilio ConversationRelay and ElevenLabs TTS.

## ✨ Key Capabilities

- **⚡ Gemini 2.0 Flash Integration**: Built for speed and responsiveness in voice contexts.
- **🔄 Dual Mode Operation**:
  - **Outbound**: Executes structured **AHRQ RED Protocol** interviews for post-discharge follow-ups.
  - **Inbound**: Identifies patients calling in and provides personalized assistance via A2A lookup.
- **📞 Twilio ConversationRelay**: Uses WebSocket streaming for real-time bidirectional audio.
- **🎙️ Call Recording v3.4**: Records all calls and sends the `CallSid` to the Pulse Agent for multimodal analysis (Audio-First Reporting).
- **🔗 A2A Delegation**: Seamlessly hands off complex medical queries to the Pulse Agent (Medical Brain).

## 🏗️ Architecture

```
caller-agent/
├── app/
│   ├── agent.py                  # LangGraph ReAct agent & Gemini 2.0 config
│   ├── server.py                 # FastAPI server (A2A + WebSocket + TwiML)
│   ├── app_utils/
│   │   ├── conversation_relay.py # Twilio WebSocket handler
│   │   ├── llm.py                # Gemini 2.0 Model setup
│   │   └── prompts/              # System prompts (AHRQ RED 5-Phase)
│   └── tools/
│       └── call_patient.py       # Twilio outbound dialer
├── deployment/                   # Terraform infrastructure
├── tests/                        # Integration, load tests
└── Makefile                      # Dev commands
```

## 🛠️ Technology Stack

- **Model**: Gemini 2.0 Flash (Preview)
- **Framework**: LangGraph (ReAct Pattern)
- **Server**: FastAPI (Async)
- **Voice**: Twilio ConversationRelay + ElevenLabs TTS
- **Protocol**: A2A (JSON-RPC)

## 🔧 Getting Started

### Prerequisites

- Python 3.10+
- `uv` package manager
- Twilio Account (SID/Token)
- ElevenLabs Account (API Key)
- Ngrok (for local webhook testing)

### Installation

```bash
make install
```

### Configuration

Create a `.env` file:

```env
PORT=8000
GOOGLE_CLOUD_PROJECT=careflow-478811
CAREFLOW_AGENT_URL=http://localhost:8080

# Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# ElevenLabs
ELEVENLABS_API_KEY=your_key

# Local Dev
NGROK_URL=your-ngrok-url.ngrok-free.app
```

### Running Locally

To start the server (typically on port **8000**):

```bash
make local-backend
```

- **TwiML Endpoint**: `http://localhost:8000/twiml`
- **Agent Card**: `http://localhost:8000/.well-known/agent.json`

## 📡 Webhook Setup (Twilio)

1. Start Ngrok: `ngrok http 8000`
2. Update `NGROK_URL` in `.env`.
3. Configure Twilio Voice Webhook to: `https://your-ngrok-url/twiml`

## 🧪 Testing

Run standard tests:

```bash
make test
```

Launch the A2A Inspector:

```bash
make inspector
```

## 🚢 Deployment

Deploy to Google Cloud Run:

```bash
make deploy
```
