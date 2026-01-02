# CareFlow Pulse

<div align="center">

**AI-Powered Post-Hospitalization Patient Monitoring System**

A production-ready healthcare application for nurse coordinators to monitor recently discharged patients using **Gemini 3** AI agents, voice interactions, and real-time dashboard. Built with Next.js frontend and dual-agent architecture.

*Preventing readmissions through intelligent, proactive care*

[![Next.js](https://img.shields.io/badge/Next.js-16.0-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Gemini 3](https://img.shields.io/badge/Gemini-3.0-4285F4?style=flat-square&logo=google)](https://deepmind.google/technologies/gemini/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Development](#-development)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🏥 Overview

**CareFlow Pulse** is an enterprise-grade healthcare monitoring platform designed for nurse coordinators to track recently discharged patients in real-time. Powered by **Google Gemini 3** and a **dual-agent AI architecture**, the system combines:

- **CareFlow Pulse Agent**: Medical reasoning agent powered by Gemini 3 Pro with direct Firestore database access via MCP (Model Context Protocol)
- **CareFlow Caller Agent**: Voice interface agent powered by Gemini 2.0 Flash enabling natural phone conversations with patients via Twilio
- **Next.js Dashboard**: Real-time web interface for nurse coordinators with patient monitoring, alerts, and AI insights

The agents communicate using the **A2A (Agent-to-Agent) protocol**, enabling seamless delegation between voice interactions and medical data analysis.

### The Challenge

Hospital readmissions within 30 days of discharge are a critical healthcare challenge, leading to:

- Increased patient morbidity and mortality
- Significant healthcare system costs (billions annually)
- Penalties for hospitals under value-based care models
- Reduced quality of life for patients

### Our Solution

CareFlow Pulse bridges the gap between hospital discharge and full recovery by:

- **Continuous Monitoring**: 24/7 AI-powered patient surveillance
- **Voice-First Interface**: Natural phone conversations with AI using Twilio + ElevenLabs TTS
- **Real-Time Database Access**: Direct Firestore integration via MCP toolbox
- **Intelligent Agent Collaboration**: A2A protocol for seamless task delegation
- **Proactive Intervention**: Enabling nurse coordinators to act before readmission is necessary
- **Evidence-Based Care**: Clinical guidelines integrated into AI decision-making
- **Scalable Platform**: Monitor hundreds of patients without proportionally increasing staff

---

## ✨ Features

### For Nurse Coordinators

- **📊 Real-Time Dashboard**
  - Live patient status overview
  - Critical metrics at a glance (total patients, active alerts, readmission risk)
  - Patient distribution by severity
  - Resource availability tracking

- **🚨 Intelligent Alert System**
  - Three-tier severity classification (Safe, Warning, Critical)
  - AI-generated actionable recommendations
  - Priority-based alert routing
  - Automated escalation protocols

- **👥 Comprehensive Patient Profiles**
  - Complete medical history and diagnosis
  - Medication plans with adherence tracking
  - Vital signs trends and analytics
  - AI interaction timeline with insights

- **💬 AI Interaction Logs**
  - Chronological patient-AI communication history
  - Symptom reports with AI analysis
  - Recommendations and interventions
  - Audit trail for compliance

- **⚙️ Configuration Portal**
  - Alert threshold customization
  - Notification preferences
  - Team member management
  - Integration settings

### AI Agent Capabilities

#### CareFlow Pulse Agent (Medical Reasoning)
- **Firestore Database Access** via MCP toolbox
  - get_all_patients
  - get_critical_patients
  - get_patients_by_risk_level
  - get_patient_by_id
  - query_patients_by_diagnosis
  - list_collections
- **Clinical Decision Support**
  - Symptom analysis based on medical guidelines
  - Risk assessment and scoring
  - Medication interaction checks
  - Evidence-based recommendations

#### CareFlow Caller Agent (Voice Interface)
- **Natural Phone Conversations** via Twilio ConversationRelay
  - Real-time voice interaction with patients
  - Symptom collection through natural dialogue
  - ElevenLabs TTS for natural-sounding responses
  - Automatic transcription and logging
- **A2A Delegation**
  - Delegates medical queries to CareFlow Pulse Agent
  - Receives structured medical insights
  - Maintains conversation context

### Coming Soon
- 🤖 Predictive readmission risk scoring with Gemini 3's advanced reasoning
- 📊 Advanced analytics and trend detection
- 📱 Mobile app for nurse coordinators (React Native)
- 🔍 EHR integration (HL7 FHIR)
- 🖼️ Multimodal support: Photo analysis (wounds, medication compliance) via Gemini 3 Vision

---


## 🗂️ Project Structure

```
careflow/
├── careflow-agents/
│   ├── caller-agent/         # Voice agent (Gemini 2.0 Flash, Twilio, LangGraph)
│   │   ├── app/              # Core logic, agent, server, utils
│   │   ├── deployment/       # Terraform (26 .tf files), cloud configs
│   │   ├── notebooks/        # Evaluation notebooks
│   │   ├── tests/            # Integration, load, unit tests
│   │   └── tools/            # A2A Inspector (backend/frontend/scripts)
│   └── careflow-agent/       # Medical reasoning agent (Gemini 3 Pro, ADK, MCP)
│       ├── app/              # Core logic, agent, server, utils
│       ├── deployment/       # Terraform (26 .tf files), cloud configs
│       ├── notebooks/        # Evaluation notebooks
│       ├── tests/            # Integration, load, unit tests
├── docs/                     # Functional & technical specs (2662 lines)
├── mcp/                      # MCP toolbox config (Firestore integration)
├── nextjs/                   # Frontend UI (Next.js 16, React 19, shadcn/ui)
│   ├── src/
│   │   ├── app/              # App Router pages (layout, page components)
│   │   └── components/       # Reusable UI components (shadcn/ui)
│   └── public/               # Static assets
├── refs/                     # A2A latency extension, samples (JS/Python)
├── scheduler/                # Cloud Scheduler orchestrator (Terraform)
│   ├── terraform/            # Terraform config for daily jobs (4 .tf files)
│   ├── run_daily_job.py      # Test script for resilience testing
│   ├── Makefile              # Scheduler management commands
│   └── README.md             # Scheduler documentation
└── README.md                 # Central documentation
```

### Communication Flow

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  Nurse Portal   │ ◄─SSE── │  Next.js 16 API  │ ◄─HTTP─►│ CareFlow Pulse  │
│  (shadcn/ui)    │         │  (API Routes)    │         │ Agent (Gemini 3)│
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └────────┬────────┘
                                                                   │
                                                              A2A  │
                                                          (JSON-RPC)
                                                                   │
┌─────────────────┐         ┌──────────────────┐         ┌────────▼──────────┐
│                 │         │                  │         │                   │
│  Patient Phone  │ ◄─Call─►│ Twilio Relay     │ ◄─WS──► │ CareFlow Caller   │
│                 │         │ + ElevenLabs TTS │         │ Agent (Gemini 2.0)│
│                 │         │                  │         │                   │
└─────────────────┘         └──────────────────┘         └───────────────────┘
                                                                   │
                                                              MCP  │
                                                          (Toolbox)│
                                                                   │
                                                          ┌────────▼────────┐
                                                          │                 │
                                                          │  Firestore DB   │
                                                          │  (careflow-db)  │
                                                          │                 │
                                                          └─────────────────┘
```

### Protocol Integrations

**MCP (Model Context Protocol)**:
- Connects agents to Firestore database via `toolbox` executable
- Provides 6 tools for patient data queries
- Runs at `http://localhost:5000` during development

**A2A (Agent-to-Agent Protocol)**:
- JSON-RPC + SSE streaming for inter-agent communication
- Exposes AgentCard at `/.well-known/agent.json`
- Enables voice agent to delegate medical queries to main agent

**Twilio ConversationRelay**:
- WebSocket-based real-time voice streaming
- Integrates ElevenLabs TTS for natural-sounding responses
- Supports barge-in and conversational AI

### Deployment Architecture

- **CareFlow Pulse Agent**: Google Cloud Run (port 8000)
- **CareFlow Caller Agent**: Google Cloud Run (port 8080)
- **Frontend**: Vercel (Next.js optimized hosting)
- **Database**: Firestore (careflow-478811/careflow-db)
- **Voice**: Twilio + ElevenLabs
- **Monitoring**: Cloud Logging, OpenTelemetry tracing

---

## 🛠️ Tech Stack

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.3 | React framework with App Router |
| **React** | 19.2.0 | UI library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 3.x | Utility-first CSS framework |
| **shadcn/ui** | Latest | Radix UI-based component library |
| **React Query** | 5.x | Server state management |
| **React Hook Form** | 7.x | Form handling |
| **Zod** | 3.x | Schema validation |
| **Recharts** | 2.x | Data visualization |
| **Lucide React** | Latest | Icon library |

### Backend Stack (AI Agents)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10-3.12 | Backend language |
| **Gemini 3 Pro** | Preview | Main orchestrator agent with advanced reasoning |
| **Gemini 2.0** | Preview | Voice agent with ultra-low latency |
| **Google ADK** | 1.16.1+ | Agent Development Kit framework |
| **LangGraph** | 1.0.3+ | REACT agent framework (CareFlow Caller Agent) |
| **MCP (Model Context Protocol)** | Latest | Firestore database access via toolbox |
| **A2A SDK** | 0.3.9 | Agent-to-Agent communication protocol |
| **Twilio ConversationRelay** | Latest | Real-time voice streaming |
| **ElevenLabs** | Latest | Text-to-speech synthesis |
| **google-genai** | 1.52.0 | Gemini model integration |
| **langchain-google-genai** | 2.0.7+ | LangChain + Gemini integration |

### Infrastructure & Protocols

- **Google Cloud Platform**: Cloud Run, Firestore, Artifact Registry
- **Vercel**: Next.js hosting and edge network
- **MCP Protocol**: Standardized tool integration
- **A2A Protocol**: Inter-agent communication (JSON-RPC + SSE)
- **OpenTelemetry**: Distributed tracing

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10-3.12** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** and **npm** - [Install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- **Google Cloud Account** - [Sign up](https://cloud.google.com/) (free tier available)
- **Twilio Account** - [Sign up](https://www.twilio.com/) (for voice features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ChristChad-mv/careflow-pulse.git
   cd careflow-pulse
   ```

2. **Install Python dependencies**
   ```bash
   cd careflow-pulse
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r careflow-agent/requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   cd nextjs
   npm install
   cd ..
   ```

4. **Set up MCP toolbox**
   
   The `toolbox` executable at project root provides MCP integration with Firestore.
   Ensure it's executable:
   ```bash
   chmod +x toolbox
   ```

5. **Configure environment variables**

   **CareFlow Pulse Agent** (`careflow-agent/careflow_pulse_agent/.env`):
   ```env
   CAREFLOW_CALLER_URL=http://localhost:8080
   MCP_TOOLBOX_URL=http://localhost:5000
   PORT=8000
   GOOGLE_CLOUD_PROJECT=careflow-478811
   ```

   **CareFlow Caller Agent** (`careflow-agent/careflow_pulse_caller/.env`):
   ```env
   CAREFLOW_AGENT_URL=http://localhost:8000
   PORT=8080
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_phone_number
   ELEVENLABS_API_KEY=your_api_key
   ```

   **Next.js** (create `.env.local` in `nextjs/`):
   ```env
   NEXT_PUBLIC_AGENT_URL=http://localhost:8000
   ```



### Our Solution### Development



CareFlow Pulse bridges the gap between hospital discharge and full recovery by:```bash

- **Continuous Monitoring**: 24/7 AI-powered patient surveillance# Run both backend and frontend concurrently

- **Early Detection**: Identifying warning signs before they become criticalmake dev

- **Proactive Intervention**: Enabling nurse coordinators to act before readmission is necessary

- **Evidence-Based Care**: Clinical guidelines integrated into AI decision-making# Or run them separately:

- **Scalable Platform**: Monitor hundreds of patients without proportionally increasing staffmake dev-backend   # Python AI Agent on http://localhost:8000

make dev-frontend  # Next.js frontend on http://localhost:3000

---

# Test AI agent with ADK web interface

## ✨ Featuresmake adk-web       # Opens at http://localhost:8501

```

### For Nurse Coordinators

### Configuration

- **📊 Real-Time Dashboard**

  - Live patient status overview1. Copy the environment template:

  - Critical metrics at a glance (total patients, active alerts, readmission risk)```bash

  - Patient distribution by severitycp app/.env.example app/.env

  - Resource availability tracking```



- **🚨 Intelligent Alert System**2. Configure your Google Cloud settings in `app/.env`:

  - Three-tier severity classification (Safe, Warning, Critical)```env

  - AI-generated actionable recommendationsGOOGLE_CLOUD_PROJECT=your-project-id

  - Priority-based alert routingGOOGLE_CLOUD_LOCATION=us-central1

  - Automated escalation protocols```



- **👥 Comprehensive Patient Profiles**## Tech Stack

  - Complete medical history and diagnosis

  - Medication plans with adherence tracking### Frontend (Next.js)

  - Vital signs trends and analytics- **Next.js 16** - React framework with App Router & Turbopack

  - AI interaction timeline with insights- **TypeScript** - Type-safe JavaScript

- **React 19** - UI framework

- **💬 AI Interaction Logs**- **shadcn/ui** - Component library built on Radix UI

  - Chronological patient-AI communication history- **Tailwind CSS** - Utility-first CSS framework

  - Symptom reports with AI analysis- **React Query** - Server state management

  - Recommendations and interventions- **React Hook Form + Zod** - Form handling and validation

  - Audit trail for compliance

### Backend (AI Agent)

- **⚙️ Configuration Portal**- **Google ADK** - Agent Development Kit for Vertex AI

  - Alert threshold customization- **Python 3.10+** - Backend language

  - Notification preferences- **Vertex AI** - Google Cloud AI platform

  - Team member management- **uv** - Python package manager

  - Integration settings

## Available Commands

### AI Agent Capabilities

### Development

- **Symptom Analysis**- `make install` - Install all dependencies

  - Natural language processing of patient reports- `make dev` - Run both backend and frontend

  - Severity assessment based on clinical guidelines- `make dev-backend` - Run Python AI Agent only

  - Pattern recognition across multiple check-ins- `make dev-frontend` - Run Next.js only

  - Context-aware analysis (patient history, medications, comorbidities)- `make adk-web` - Launch ADK web interface for testing



- **Risk Assessment**### Linting

  - Readmission risk scoring- `make lint` - Lint both backend and frontend

  - Early warning signs detection- `make lint-backend` - Lint Python code (ruff + mypy)

  - Medication non-adherence alerts- `make lint-frontend` - Lint Next.js code (ESLint)

  - Social determinants of health consideration

### Deployment

- **Automated Decision Support**- `make deploy-agent` - Deploy AI Agent to Vertex AI Agent Engine

  - Evidence-based recommendations- `make deploy-frontend` - Deploy Next.js to Vercel

  - Escalation pathway suggestions

  - Care coordination support### Cleanup

  - Patient education content generation- `make clean` - Remove build artifacts and dependencies



---## Features



## 🏗️ Architecture### Current

- 📊 Real-time patient monitoring dashboard

CareFlow Pulse follows a modern, scalable monorepo architecture with clear separation of concerns:- 🚨 Critical alerts system with severity levels

- 👥 Patient management with detailed profiles

```- 💬 AI interaction logs and timeline

careflow-pulse/- ⚙️ Configuration portal for system settings

├── app/                          # 🤖 AI Agent Backend (Python)- 📱 Responsive design for all devices

│   ├── agent.py                  # LLM agent definition with clinical instructions

│   ├── config.py                 # Environment and deployment configuration### Coming Soon (AI Agent)

│   ├── agent_engine_app.py       # Agent Engine deployment logic- 🤖 AI-powered patient monitoring

│   └── utils/                    # Helper utilities (GCS, tracing, typing)- 📲 SMS integration for patient check-ins

│- 🔍 Symptom analysis and risk assessment

├── nextjs/                       # ⚛️  Frontend Application (Next.js)- ⚡ Real-time alert generation

│   ├── app/                      # Next.js 16 App Router- 📊 Predictive readmission risk scoring

│   │   ├── (dashboard)/         # Protected dashboard routes
│   │   │   ├── dashboard/       # Main dashboard page
│   │   │   ├── alerts/          # Critical alerts page
│   │   │   ├── patients/        # Patient list page
│   │   │   ├── patient/[id]/    # Dynamic patient detail page
│   │   │   └── config/          # Configuration portal
│   │   ├── api/                 # API routes (future SSE endpoints)
│   │   ├── layout.tsx           # Root layout with providers
│   │   └── page.tsx             # Landing page (redirect to dashboard)
│   │
│   ├── src/
│   │   ├── components/          # Reusable React components
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   ├── layout/         # AppSidebar, MainLayout
│   │   │   └── NavLink.tsx     # Navigation component
│   │   ├── data/               # Mock data (development)
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utility functions
│   │   └── types/              # TypeScript type definitions
│   │
│   └── public/                  # Static assets
│
├── Makefile                     # 🛠️  Development orchestration
├── pyproject.toml               # 📦 Python dependencies (Google ADK)
├── README.md                    # This file
├── ADK_DEPLOYMENT_GUIDE.md      # Comprehensive ADK deployment guide
└── NEXTJS_VERCEL_DEPLOYMENT_GUIDE.md  # Frontend deployment guide
```

### Communication Flow

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  Nurse Portal   │ ◄─SSE── │  Next.js API     │ ◄─RPC── │  AI Agent       │
│  (React UI)     │         │  (API Routes)    │         │  (Vertex AI)    │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
         │                           │                            │
         │                           │                            │
         ▼                           ▼                            ▼
  User Actions              Real-time Updates           Symptom Analysis
  Alert Review              Session Management          Risk Assessment
  Patient Monitoring        CORS Handling               Alert Generation
```

### Deployment Architecture

- **Frontend**: Vercel (Next.js optimized hosting)
- **AI Agent**: Google Cloud Vertex AI Agent Engine
- **Data Storage**: Google Cloud Storage (logs, artifacts)
- **Authentication**: Service Account based (Agent Engine)
- **Monitoring**: Cloud Logging, OpenTelemetry tracing

---

## 🛠️ Tech Stack

### Frontend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.3 | React framework with App Router |
| **React** | 19.2.0 | UI library |
| **TypeScript** | 5.x | Type-safe JavaScript |
| **Tailwind CSS** | 3.x | Utility-first CSS framework |
| **shadcn/ui** | Latest | Radix UI-based component library |
| **React Query** | 5.x | Server state management |
| **React Hook Form** | 7.x | Form handling |
| **Zod** | 3.x | Schema validation |
| **Recharts** | 2.x | Data visualization |
| **Lucide React** | Latest | Icon library |
| **date-fns** | 3.x | Date utilities |

### Backend Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10-3.12 | Backend language |
| **Google ADK** | 1.6.1+ | Agent Development Kit |
| **Vertex AI** | Latest | Google Cloud AI platform |
| **uv** | Latest | Fast Python package manager |
| **python-dotenv** | Latest | Environment variable management |
| **ruff** | 0.4.6+ | Python linter |
| **mypy** | 1.15.0 | Static type checker |

### Infrastructure

- **Google Cloud Platform**: Vertex AI, Cloud Storage, Cloud Run, Artifact Registry
- **Vercel**: Next.js hosting and edge network
- **OpenTelemetry**: Distributed tracing
- **Cloud Logging**: Application logging and monitoring

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10-3.12** - [Download Python](https://www.python.org/downloads/)
- **uv** (Python package manager) - [Install uv](https://docs.astral.sh/uv/)
- **Node.js 18+** and **npm** - [Install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)
- **Google Cloud Account** - [Sign up](https://cloud.google.com/) (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ChristChad-mv/careflow-pulse.git
   cd careflow-pulse
   ```

2. **Install all dependencies**
   ```bash
   make install
   ```
   This command installs both Python (AI agent) and Node.js (frontend) dependencies.

3. **Set up environment variables**
   ```bash
   # Copy the environment template
   cp app/.env.example app/.env
   
   # Edit app/.env with your configuration
   nano app/.env  # or use your preferred editor
   ```

   **Required environment variables:**
   ```env
   # Google Cloud Configuration
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_CLOUD_STAGING_BUCKET=your-staging-bucket
   
   # Agent Configuration
   AGENT_NAME=careflow-pulse-agent
   MODEL=gemini-3-flash-preview
   
   # Vertex AI Configuration
   GOOGLE_GENAI_USE_VERTEXAI=True
   ```

4. **Authenticate with Google Cloud**
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

---

## 💻 Development

### Running the Application

#### Option 1: Run Both Services Concurrently (Recommended)

```bash
make dev
```

This starts:
- **AI Agent Backend** at `http://localhost:8000`
- **Next.js Frontend** at `http://localhost:3000`

#### Option 2: Run Services Separately

```bash
# Terminal 1: Start AI Agent Backend
make dev-backend

# Terminal 2: Start Next.js Frontend
make dev-frontend
```

### Testing the AI Agent

Launch the ADK web interface to test agent interactions:

```bash
make adk-web
```

Opens at `http://localhost:8501` - allows direct chat with the AI agent.

### Code Quality

```bash
# Lint everything
make lint

# Lint Python code only
make lint-backend

# Lint Next.js code only
make lint-frontend
```

### Available Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies (Python + Node.js) |
| `make dev` | Run both backend and frontend concurrently |
| `make dev-backend` | Run Python AI Agent only |
| `make dev-frontend` | Run Next.js frontend only |
| `make adk-web` | Launch ADK web interface for testing |
| `make lint` | Lint both backend and frontend |
| `make lint-backend` | Lint Python code (ruff + mypy) |
| `make lint-frontend` | Lint Next.js code (ESLint) |
| `make deploy-agent` | Deploy AI agent to Vertex AI Agent Engine |
| `make deploy-frontend` | Deploy Next.js to Vercel |
| `make clean` | Remove build artifacts and dependencies |

---

## 🚢 Deployment

### Prerequisites for Deployment

#### 1. Google Cloud Setup (for AI Agent)

Follow the comprehensive [ADK Deployment Guide](./ADK_DEPLOYMENT_GUIDE.md) which covers:
- Google Cloud project creation
- Required API enablement (5 APIs)
- IAM permissions configuration
- Storage bucket creation
- Service account setup

#### 2. Vercel Setup (for Frontend)

Follow the [Next.js Vercel Deployment Guide](./NEXTJS_VERCEL_DEPLOYMENT_GUIDE.md) which covers:
- Vercel account configuration
- Environment variable setup
- Service account key generation
- Production deployment steps

### Quick Deployment

Once prerequisites are complete:

```bash
# Deploy AI agent to Vertex AI Agent Engine
make deploy-agent

# Deploy frontend to Vercel (requires Vercel CLI)
make deploy-frontend
```

### Production Environment Variables

Ensure these are configured in your production environments:

**Vercel (Frontend):**
- `GOOGLE_CLOUD_PROJECT`
- `REASONING_ENGINE_ID`
- `GOOGLE_SERVICE_ACCOUNT_KEY_BASE64`
- `AGENT_ENGINE_ENDPOINT`
- `GOOGLE_CLOUD_LOCATION`
- `ADK_APP_NAME`

**Agent Engine (Backend):**
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_GENAI_USE_VERTEXAI`
- `MODEL`
- `AGENT_NAME`

---

## 📁 Project Structure

### Frontend (`nextjs/`)

```
nextjs/
├── app/                          # Next.js 16 App Router
│   ├── (dashboard)/             # Route group with shared sidebar layout
│   │   ├── layout.tsx           # Sidebar layout wrapper
│   │   ├── dashboard/page.tsx   # Main dashboard (KPIs, charts)
│   │   ├── alerts/page.tsx      # Critical alerts list
│   │   ├── patients/page.tsx    # Patient directory
│   │   ├── patient/[id]/page.tsx # Patient detail view
│   │   └── config/page.tsx      # Configuration portal
│   ├── api/                     # API routes (future)
│   ├── layout.tsx               # Root layout (fonts, providers, metadata)
│   ├── providers.tsx            # React Query provider
│   └── page.tsx                 # Landing page (redirects to dashboard)
│
├── src/
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components (44 components)
│   │   ├── layout/              # AppSidebar, MainLayout
│   │   └── NavLink.tsx          # Navigation link component
│   ├── data/                    # Mock patients, alerts, interactions
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utility functions
│   └── types/                   # TypeScript type definitions
│
└── public/                      # Static assets
```

### Backend (`careflow-agent/`)

```
careflow-agent/
├── careflow_pulse_agent/        # Main Medical Agent (Port 8000)
│   ├── agent.py                 # ADK agent with MCP tools
│   │                            # - CareFlowAgent class
│   │                            # - MCP toolbox integration (6 Firestore tools)
│   │                            # - Clinical reasoning and decision support
│   │                            # - A2A tools for caller delegation
│   │
│   ├── server.py                # A2A server for inter-agent communication
│   │                            # - CareFlowAgentExecutor
│   │                            # - AgentCard definition
│   │                            # - JSON-RPC + SSE endpoints
│   │
│   ├── .env                     # Environment configuration
│   ├── Dockerfile               # Container with MCP toolbox
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Agent-specific documentation
│
├── careflow_pulse_caller/       # Voice Interface Agent (Port 8080)
│   ├── agent.py                 # LangGraph REACT agent
│   │                            # - Voice interaction handling
│   │                            # - A2A tools for medical agent delegation
│   │                            # - Conversation state management
│   │                            # - Twilio ConversationRelay integration
│   │
│   ├── server.py                # A2A server + Twilio webhook endpoints
│   │                            # - CallerAgentExecutor
│   │                            # - AgentCard with voice skills
│   │                            # - /twiml endpoint for Twilio
│   │
│   ├── config.yaml              # Agent configuration
│   ├── .env                     # Environment configuration
│   ├── Dockerfile               # Container for caller agent
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Agent-specific documentation
│
├── mcp/
│   └── tools.yaml               # MCP toolbox configuration
│                                # - Firestore database connection
│                                # - Patient query tool definitions
│
├── requirements.txt             # Shared dependencies (ADK, LangGraph, A2A)
└── deploy.sh                    # Cloud Run deployment script
```

---

## 🎨 Design System

CareFlow Pulse uses a **medical-grade dark theme** optimized for healthcare environments:

### Color Palette

- **Primary**: Soft blue (`#60A5FA`) - Trust, clarity, medical professionalism
- **Background**: Deep navy (`#0F172A`) - Reduces eye strain for long shifts
- **Safe Status**: Emerald green (`#10B981`) - Positive, stable condition
- **Warning Status**: Amber orange (`#F59E0B`) - Caution, needs attention
- **Critical Status**: Crimson red (`#EF4444`) - Urgent, immediate action

### Typography

- **Font Family**: Inter (Google Fonts) - Highly legible, professional
- **Font Sizes**: Modular scale optimized for medical data density

### Components

44 shadcn/ui components provide:
- Consistent design language
- Accessibility (WCAG AA compliance)
- Responsive layouts
- Dark mode optimized

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines

- Follow existing code style (ESLint + Ruff configs)
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

---

## 🗺️ Roadmap

### Phase 1: Core Platform (Current)
- ✅ Next.js frontend with dashboard
- ✅ Dual-agent AI architecture (CareFlow Pulse + Caller agents)
- ✅ MCP protocol integration for Firestore database access
- ✅ A2A protocol for inter-agent communication
- ✅ Dockerfiles and Cloud Run deployment configuration
- 🔄 Twilio ConversationRelay + ElevenLabs TTS integration
- 🔄 Production deployment to Cloud Run

### Phase 2: AI Integration
- ⏳ Real-time patient symptom analysis via voice calls
- ⏳ Risk scoring algorithm based on medical guidelines
- ⏳ Automated alert generation for nurse coordinators
- ⏳ Voice-to-dashboard integration (SSE streaming)
- ⏳ EHR system integration (HL7 FHIR) via MCP extensions

### Phase 3: Clinical Features
- ⏳ Advanced medication interaction detection
- ⏳ Vital signs monitoring from wearable devices
- ⏳ Multi-language support (French, English, Arabic)
- ⏳ Nurse coordinator mobile app
- ⏳ Patient education content generation

### Phase 4: Enterprise Features
- ⏳ Multi-tenant architecture for multiple hospitals
- ⏳ Role-based access control (RBAC)
- ⏳ HIPAA compliance certification
- ⏳ Advanced analytics and reporting dashboards
- ⏳ Integration with French hospital systems

### Phase 5: Market Expansion
- ⏳ Demo pilot with French hospitals
- ⏳ Patient mobile app (React Native)
- ⏳ Telehealth video integration
- ⏳ AI-powered care plan recommendations
- ⏳ International healthcare system support

---

<div align="center">

**Built with ❤️ for healthcare professionals**

*Empowering nurse coordinators to save lives, one patient at a time*

[GitHub](https://github.com/ChristChad-mv/careflow-pulse) • [Documentation](./ADK_DEPLOYMENT_GUIDE.md)

</div>
