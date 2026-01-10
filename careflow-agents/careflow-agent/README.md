# CareFlow Pulse Monitoring Agent

Medical monitoring and analysis agent powered by **Gemini 3.0 Pro**. Analyzes patient data, manages wellness reports, and coordinates with the Caller Agent via A2A protocol to maintain patient health loops.

## ✨ Features

- 🏥 **Data Analysis**: Processes complex patient records and hospitalization data.
- 🚨 **Alert Management**: Detects critical health triggers and initiates follow-up loops.
- 🔄 **A2A Protocol**: Standards-based communication with the Caller Agent for patient outreach.
- 🛡️ **HIPAA Alignment**: Integrated with Model Armor and DLP for secure medical data handling.
- 📝 **Report Generation**: Automatically generates structured patient wellness summaries.

## 🏗️ Architecture

```
careflow-agent/
├── app/                          # Core application code
│   ├── agent.py                  # ADK Orchestration layer (Gemini 2.0 Flash)
│   ├── server.py                 # FastAPI server (A2A Protocol)
│   ├── app_utils/                # Utilities and helpers
│   │   ├── config_loader.py      # Environment configuration
│   │   ├── telemetry.py          # OpenTelemetry instrumentation
│   │   └── executor/
│   │       └── careflow_executor.py # A2A protocol executor
│   ├── schemas/                  # Versioned A2A metadata
│   │   └── agent_card/v1/        # A2A Discovery documents
│   ├── tools/                    # Specialized agent toolsets
│   │   ├── a2a_tools.py          # Inter-agent communication tools
│   │   └── mcp__tool_loader.py   # MCP Toolbox integration
│   └── callbacks/                # Agent lifecycle hooks
├── deployment/                    # Terraform infrastructure
├── tests/                         # Unit and integration tests
├── Makefile                       # Development & Ops commands
└── pyproject.toml                 # Dependencies (uv)
```

## 🚀 Technology Stack

- **LLM**: Gemini 2.0 Flash
- **Framework**: Google Agent Development Kit (ADK)
- **Server**: FastAPI + uvicorn
- **Security**: Model Armor + DLP
- **Protocol**: A2A (Agent-to-Agent)
- **Dependency Management**: uv
- **Observability**: OpenTelemetry + Traceloop

## 📋 Prerequisites

- **Python 3.10-3.13**
- **uv** package manager ([installation](https://docs.astral.sh/uv/getting-started/installation/))
- **Google Cloud Project** with Vertex AI, DLP, and Model Armor enabled.

## 🔧 Setup

### 1. Install Dependencies

```bash
# Install project dependencies
make install
```

### 2. Configure Environment Variables

The agent uses a `.env` file for local development. Standardize your ports for unique communication:

```bash
# Server Configuration
PORT=8080

# A2A Loopback - Caller Agent URL
CAREFLOW_CALLER_URL=http://localhost:8000
```

## 🎯 Running the Agent

### Development Mode (with hot-reload)

```bash
make local-backend
```

The agent will be accessible at **<http://localhost:8080>** with:

- 🤖 Agent Card: `http://localhost:8080/.well-known/agent.json`

## 🧪 Development Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make local-backend` | Launch local development server on port 8080                                                |
| `make inspector`     | Launch A2A Protocol Inspector                                                               |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (ruff, mypy)                                                       |

## 🔍 A2A Protocol Testing

Launch the A2A inspector to test agent interactions:

```bash
make inspector
```

Inspector UI: **<http://localhost:5001>**
Connect to: `http://localhost:8080/.well-known/agent.json`

## 🚢 Deployment

Deploy to Google Cloud Run:

```bash
make deploy
```

## 🤝 Integration with Caller Agent

The Pulse Agent acts as the analytical brain:

1. Receives task from Caller Agent (e.g., "Review patient symptoms")
2. Executes analysis and accesses hospitalization history
3. Returns status or delegatable tasks back to the Caller Agent
4. Maintains full observability spans for inter-agent calls

## 🎨 Code Quality

The codebase utilizes professional headers and follows strict typing:

- **Python Headers**: Every core module contains a descriptive docstring.
- **Versioning**: Agent schemas are versioned in `app/schemas/agent_card/v1/`.
