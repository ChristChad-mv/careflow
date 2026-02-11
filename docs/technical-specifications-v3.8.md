# **CareFlow Pulse: Technical Specifications (v3.8)**

| | |
| :--- | :--- |
| **Document Version:** | 3.8 |
| **Date:** | 2026-02-11 |
| **Status:** | **Official** |
| **Author:** | Christ |

---

## **Revision History**

| Version | Date | Author | Changes |
| :--- | :--- | :--- | :--- |
| 1.0 | 2025-12-20 | Christ | Initial Draft - Basic architecture overview |
| 2.0 | 2025-12-23 | Christ | Complete rewrite with comprehensive database structure, API endpoints, and implementation details |
| 3.0 | 2025-12-26 | Christ | Major architecture update: Dual-agent system (CareFlow Pulse + Caller), MCP protocol integration, A2A inter-agent communication, Twilio ConversationRelay, Cloud Run deployment |
| 3.1 | 2025-12-26 | Christ | Major architecture update: Dual-agent system (CareFlow Pulse + Caller), MCP protocol integration, A2A inter-agent communication, Twilio ConversationRelay, Cloud Run deployment (v2) |
| 3.2 | 2026-01-02 | Christ | Cloud Scheduler Infrastructure as Code: Terraform configuration with multi-environment deployment (staging/prod), OIDC authentication, automated retry logic, comprehensive monitoring setup |
| 3.3 | 2026-01-10 | Christ | Advanced AI Security: Integrated Google Model Armor (v0.3.0) with Fail-Closed architecture, synchronized regional endpoints across dual-agent system, and established comprehensive Security & Compliance specs. |
| 3.4 | 2026-01-14 | Christ | Audio-First Reporting Architecture: Pivoted from transcript-based to audio-based analysis. Caller Agent records calls; Pulse Agent fetches raw audio and leverages Gemini 3's native multimodal analysis. |
| 3.5 | 2026-01-16 | Christ | Real-Time Dashboard Alerts: Implemented Firestore `onSnapshot` listeners for instant alert propagation. Added `useAlerts` hook, `AlertsRealtime` component, and real-time sidebar badge updates. |
| 3.6 | 2026-01-16 | Christ | Caller Agent Documentation: Added AHRQ RED 5-phase interview protocol, Dual Mode (Outbound/Inbound), Model Armor security reference. Removed code examples per documentation standards. |
| 3.7 | 2026-01-16 | Christ | Pulse Agent Documentation: Added 5 Core Workflows, CareFlowAgent architecture pattern, expanded Tools section (MCP/A2A/Audio). Removed code examples per documentation standards. |
| 3.8 | 2026-01-24 | Christ | **Missed Call Detection & Retry System**: Comprehensive Twilio status tracking (no-answer/busy/failed), A2A CALL_FAILED messaging, Firestore interaction subcollection logging, Cloud Tasks retry scheduling with exponential backoff, retry limits (max 3 attempts). |

---

## **Table of Contents**

### 1. Introduction

- 1.1. Purpose of this Document
- 1.2. Intended Audience
- 1.3. Document Scope
- 1.4. References & Dependencies

### 2. System Architecture Overview

- 2.1. High-Level Architecture Diagram
- 2.2. Technology Stack
- 2.3. Component Interaction Flow
- 2.4. Deployment Architecture
- 2.5. Audio-First Reporting Architecture
- 2.6. Missed Call Detection & Retry System (NEW v3.8)

### 3. Database Design (Firestore)

- 3.1. Overview & Design Principles
- 3.2. Collection: `/patients`
- 3.3. Sub-Collection: `/patients/{patientId}/interactions`
- 3.4. Sub-Collection: `/patients/{patientId}/medicationLog`
- 3.5. Collection: `/alerts`
- 3.6. Collection: `/users`
- 3.7. Indexes & Query Optimization
- 3.8. Security Rules
- 3.9. Data Migration & Seeding

### 4. Backend: AI Agent System (Google ADK)

- 4.1. Agent Architecture Overview
- 4.2. Pulse Agent (Orchestrator & Intelligence)
- 4.3. Caller Agent (Voice & Messaging Interface)
- 4.4. Clinical Reasoning: Triage & Analysis
- 4.5. Clinical Reasoning: Medical Synthesis
- 4.6. ADK Tools & Integrations
- 4.7. Prompt Engineering Strategy
- 4.8. Error Handling & Fallback Logic
- 4.9. Native Multi-Language Support

### 5. Backend: API Endpoints

- 5.1. Endpoint Overview
- 5.2. `POST /api/careflow/trigger-scheduled-calls`
- 5.3. `POST /api/careflow/twilio-sms`
- 5.4. `POST /api/careflow/voice-alert`
- 5.5. Authentication & Authorization
- 5.6. Rate Limiting & Security

### 6. External Integrations

- 6.1. Twilio ConversationRelay
- 6.2. ElevenLabs TTS
- 6.3. Google Cloud Platform (GCP)

### 7. Frontend: Next.js Application

- 7.1. Technology Stack
- 7.2. Architecture Principles
- 7.3. Real-Time Data Patterns 
- 7.4. Key Components & Pages

### 8. Data Flow & User Journeys

- 8.1. Journey: Automated Morning Rounds
- 8.2. Journey: Critical Symptom Triage

### 9. Security & Compliance

- 9.1. Data Encryption & Integrity
- 9.2. Multi-Tenant Isolation
- 9.3. AI Safety & Model Armor
- 9.4. HIPAA Compliance Considerations
- 9.5. Audit Logging
- 9.6. Reference Documentation

### 10. Configuration & Environment Variables

- 10.1. Backend Environment Variables (The Fleet)

### 11. Deployment Guide

- 11.2. Infrastructure as Code (Terraform)
- 11.2. Cloud Scheduler Deployment (Terraform)
- 11.3. Frontend Deployment (Vercel)

### 12. Testing Strategy & Benchmarks

- 12.1. Benchmark-Driven Architecture
  - 12.1.1. Model Latency Benchmark
  - 12.1.2. Security Latency Benchmark (Model Armor)
- 12.2. Protocol Verification ("Teach-Back" Evaluation)
- 12.3. Audio Handoff Testing (v3.4)
- 12.4. Load Testing (Locust)
- 12.5. Unit & Integration Testing
- 12.6. Manual Voice Testing

### 13. Performance Optimization

- 13.1. Voice Latency Hierarchy
- 13.2. Database Performance

### 14. Error Handling & Monitoring

- 14.1. Clinical Safety Handover
- 14.2. Operational Monitoring

### 15. Future Enhancements & Roadmap

- 15.1. Vision-Based Adherence (v3.5)
- 15.2. EHR Integration (v4.0)
- 4.9. Native Multi-Language Support

### **Appendices**

- **Appendix A:** API Request/Response Examples
- **Appendix B:** Database Schema Diagrams
- **Appendix C:** Firestore Security Rules (Complete)
- **Appendix D:** Environment Variable Reference
- **Appendix E:** Glossary of Terms

---

## **1. Introduction**

### **1.1. Purpose of this Document**

This Technical Specification document provides a comprehensive, implementation-ready blueprint for **CareFlow Pulse**, an AI-powered post-hospitalization patient monitoring system. It is designed to bridge the gap between high-level functional requirements and actual code implementation by providing:

- **Complete database schema** with field-level specifications
- **Detailed API endpoint definitions** with request/response formats
- **Integration specifications** for third-party services (Twilio, ElevenLabs, Google Cloud)
- **Architecture diagrams** showing component interactions
- **Security and compliance guidelines** for healthcare data handling
- **Deployment procedures** for production environments

This document serves as the single source of truth for developers, architects, DevOps engineers, and QA teams working on CareFlow Pulse. It is meant to be read in conjunction with the **Functional Specifications (v2.0)**, which defines the *what* and *why*, while this document focuses on the *how*.

---

### **1.2. Intended Audience**

This document is written for technical stakeholders involved in the development, deployment, and maintenance of CareFlow Pulse:

| Role | How to Use This Document |
| :--- | :--- |
| **Backend Developers** | Sections 3-6: Database design, ADK agent implementation, API endpoints, and external integrations |
| **Frontend Developers** | Sections 3, 7: Database schema for data models, Next.js application structure, authentication, and real-time data sync |
| **DevOps Engineers** | Sections 10-11: Environment configuration, deployment procedures, CI/CD pipeline setup |
| **QA Engineers** | Sections 8, 12: User flow scenarios, testing strategy, and test data requirements |
| **Solutions Architects** | Sections 2, 9, 13-14: System architecture, security, performance optimization, and monitoring |
| **Project Managers** | Sections 1-2, 15: Overview, architecture, and future roadmap for planning and stakeholder communication |

**Prerequisites:** Readers should have familiarity with:

- Modern web development (TypeScript, React, Next.js)
- Python backend development
- Cloud platforms (Google Cloud Platform)
- NoSQL databases (Firestore)
- RESTful API design
- Healthcare data sensitivity and compliance basics

---

### **1.3. Document Scope**

#### **In Scope:**

This technical specification covers the complete end-to-end implementation of CareFlow Pulse v1.0, including:

✅ **Database Architecture**

- Complete Firestore collection and sub-collection schemas
- Field definitions with types, constraints, and validation rules
- Index strategies for query optimization
- Security rules for data access control

✅ **Backend AI Agent System**

- Multi-agent architecture using Google ADK (Agent Development Kit)
- Agent roles, responsibilities, and interaction patterns
- Prompt engineering strategies for healthcare context
- Integration with Vertex AI Agent Engine

✅ **API Layer**

- All REST endpoints exposed by the backend
- Webhook endpoints for external service callbacks
- Authentication and authorization mechanisms
- Request/response schemas and error handling

✅ **External Service Integrations**

- Twilio for voice calls and SMS messaging
- Twilio ConversationRelay + ElevenLabs for AI-powered voice conversations
- Google Cloud Scheduler for time-based triggers
- Configuration and webhook setup for each service

✅ **Frontend Application**

- Next.js 16 application structure with App Router
- NextAuth authentication with role-based access control
- Real-time dashboard with Firestore listeners
- UI components and page-level specifications

✅ **Security & Compliance**

- Data encryption (at rest and in transit)
- Healthcare data handling best practices
- HIPAA compliance considerations
- Audit logging requirements

✅ **Deployment & Operations**

- Environment configuration for dev, staging, and production
- Deployment procedures for all components
- Monitoring, logging, and alerting strategies

#### **Out of Scope (Future Versions):**

The following features are acknowledged as important but are **not included in v1.0**:

❌ **EHR System Integration** - Direct integration with Electronic Health Record systems like Epic, Cerner, or MEDITECH will be addressed in v2.0

❌ **Patient-Facing Mobile Application** - A native iOS/Android app for patients is planned for v1.5

❌ **Advanced Analytics & Reporting** - Predictive models for readmission risk, custom report builders, and data visualization beyond the basic dashboard

✅ **Multi-Language Support** - Natively supported by Gemini 1.5/2.0/3.0 architecture. The system handles English, Spanish, French, Mandarin, Japanese, Korean, and more without complex configuration.

❌ **Billing & Insurance Integration** - Revenue cycle management features are out of scope for the MVP

❌ **Wearable Device Integration** - Real-time vitals from Apple Watch, Fitbit, etc., will be explored in v2.0

❌ **FHIR API** - While important for interoperability, FHIR compliance is targeted for v2.0

---

### **1.4. References & Dependencies**

#### **Related Documents**

This technical specification should be read alongside the following documents:

1. **[Functional Specifications v2.0](/docs/functional-specifications-v1.1.md)** - Defines user stories, personas, and business requirements
2. **[ADK Deployment Guide](/ADK_DEPLOYMENT_GUIDE.md)** - Step-by-step guide for deploying the AI agent to Vertex AI
3. **[Next.js Vercel Deployment Guide](/NEXTJS_VERCEL_DEPLOYMENT_GUIDE.md)** - Frontend deployment procedures
4. **[Security Audit Report](/nextjs/SECURITY_AUDIT.md)** - Security assessment and recommendations

#### **External Documentation**

The following external resources are referenced throughout this document:

| Technology | Documentation URL |
| :--- | :--- |
| **Google ADK** | [https://cloud.google.com/vertex-ai/generative-ai/docs/agent-development-kit](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-development-kit) |
| **LangGraph** | [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/) |
| **MCP Protocol** | [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/) |
| **A2A Protocol** | [https://github.com/google/generative-ai-docs/tree/main/a2a](https://github.com/google/generative-ai-docs/tree/main/a2a) |
| **Firestore** | [https://firebase.google.com/docs/firestore](https://firebase.google.com/docs/firestore) |
| **Next.js 16** | [https://nextjs.org/docs](https://nextjs.org/docs) |
| **NextAuth v5** | [https://authjs.dev/](https://authjs.dev/) |
| **Twilio ConversationRelay** | [https://www.twilio.com/docs/voice/conversationrelay](https://www.twilio.com/docs/voice/conversationrelay) |
| **Twilio SMS** | [https://www.twilio.com/docs/sms](https://www.twilio.com/docs/sms) |
| **ElevenLabs** | [https://elevenlabs.io/docs](https://elevenlabs.io/docs) |
| **Google Cloud Run** | [https://cloud.google.com/run/docs](https://cloud.google.com/run/docs) |
| **shadcn/ui** | [https://ui.shadcn.com/](https://ui.shadcn.com/) |

#### **Technology Stack Dependencies**

**Backend:**

- Python 3.10-3.12
- google-adk >= 1.16.0 (CareFlow Pulse Agent)
- langgraph (CareFlow Caller Agent)
- langchain-google-genai >= 2.0.7
- a2a-sdk (Agent-to-Agent communication)
- toolbox-core (MCP protocol)
- python-dotenv
- Deployed on Google Cloud Run (2 separate services)

**Frontend:**

- Node.js 18+ / npm or bun
- Next.js 16.0.9
- React 19.2.0
- NextAuth 5.0.0-beta.30
- TypeScript 5.8.3
- Tailwind CSS 3.4.17
- shadcn/ui component library
- Deployed on Vercel

**Database:**

- Google Cloud Firestore (NoSQL document database)

**External Services:**

- Twilio ConversationRelay (Real-time voice streaming)
- Twilio SMS (Text messaging)
- ElevenLabs (Text-to-speech synthesis)
- Google Cloud Run (Container hosting)
- Google Cloud Firestore (Database)
- Google Cloud Artifact Registry (Container images)

#### **Development & DevOps**

| Tool | Purpose |
| :--- | :--- |
| **Makefile** | Development workflow orchestration (install, dev, deploy) |
| **Git** | Version control (GitHub repository) |
| **npm/bun** | Frontend package management |
| **uv** | Backend package management |
| **Environment Files** | `.env` for configuration management |

---

## **2. System Architecture Overview**

### **2.1. High-Level Architecture Diagram**

CareFlow Pulse is built on a **modern dual-agent architecture** using cutting-edge protocols (MCP, A2A) for healthcare data access and inter-agent communication. The system separates concerns between medical intelligence, voice interaction, and user interfaces.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CAREFLOW PULSE ARCHITECTURE v3.4                    │
│           Dual-Agent System with MCP, A2A & Audio-First Reporting          │
│                     MULTI-TENANT FLEET (1 Agent / Hospital)                │
└────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   PATIENTS   │
                              │  (End Users) │
                              └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │  Phone   │    │   SMS    │    │  (Future)│
              │  Calls   │    │ Messages │    │ Dashboard│
              └────┬─────┘    └────┬─────┘    └──────────┘
                   │               │
           ┌───────▼───────────────▼────────┐
           │                                 │
           │  TWILIO CONVERSATIONRELAY       │
           │  • Real-time Voice Streaming    │
           │  • WebSocket Connection         │
           │  • SMS Gateway                  │
           └──────────┬──────────────────────┘
                      │
                      │ Webhooks (/twiml)
                      ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  GOOGLE CLOUD RUN (The Fleet)               │
    │         (One Service per Hospital for Isolation)            │
    │                                                             │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │   CareFlow Caller Agent (Port 8080)                 │    │
    │  │   (Shared Service or Dedicated)                     │    │
    │  └──────────────────┬──────────────────────────────────┘    │
    │                     │                                         │
    │                     │ A2A Protocol (JSON-RPC + SSE)          │
    │                     ▼                                         │
    │  ┌─────────────────────────────────────────────────────┐    │
    │  │   AGENT FLEET (Medical Intelligence)                │    │
    │  │                                                     │    │
    │  │   [Service: careflow-agent-hosp001]                 │    │
    │  │   • Env: HOSPITAL_ID=HOSP01                         │    │
    │  │                                                     │    │
    │  │   [Service: careflow-agent-hosp002]                 │    │
    │  │   • Env: HOSPITAL_ID=HOSP02                         │    │
    │  │                                                     │    │
    │  │   ... (Scales Horizontally)                         │    │
    │  └──────────────────┬──────────────────────────────────┘    │
    │                     │                                         │
    └─────────────────────┼───────────────────────────────────────┘
                          │
                          │ MCP Protocol (Restricted by HOSPITAL_ID)
                          ▼
              ┌─────────────────────────┐
              │    MCP TOOLBOX          │
              │    (Executable)         │
              └────────┬────────────────┘
                       │
                       │ Firestore SDK
                       ▼
    ┌─────────────────────────────────────────────────────┐
    │                                                       │
    │           GOOGLE CLOUD FIRESTORE                     │
    │       (Database: careflow-478811/careflow-db)        │
    │                                                       │
    │  Collections (Logical Isolation via hospitalId):     │
    │  • /patients                    [where hospitalId=X]│
    │  • /alerts                      [where hospitalId=X]│
    │  • /users                       [where hospitalId=X]│
    │                                                       │
    └──────────────────┬────────────────────────────────────┘
                       │
                       │ Real-time Sync (onSnapshot)
                       ▼
    ┌─────────────────────────────────────────────────────┐
    │           NEXT.JS FRONTEND (Vercel)                  │
    │     (Multi-Tenant Dashboard via Auth Context)        │
    └─────────────────────────────────────────────────────┘

ORCHESTRATION (The Dispatcher):
Cloud Scheduler (Daily) --> [Dispatcher Function] --> Loops Active Hospitals --> Triggers Specific Agent URL
```

**Key Architectural Principles:**

1. **Dual-Agent Specialization**: Separate agents for voice interaction (Caller) and medical intelligence (Pulse)
2. **MCP Protocol**: Standardized toolbox integration for Firestore database access
3. **A2A Protocol**: Inter-agent communication using JSON-RPC + SSE streaming
4. **Audio-First Reporting (v3.4)**: Raw audio analysis via Gemini 3 multimodal instead of transcripts
5. **Voice-First Interface**: Natural phone conversations via Twilio ConversationRelay + ElevenLabs
6. **Real-Time Sync**: Firestore acts as the single source of truth with live updates to frontend
7. **Containerized Deployment**: Both agents run as separate Cloud Run services
8. **Cloud-Native**: Leverages managed Google Cloud services for scalability and reliability

---

### **2.2. Technology Stack**

#### **Frontend (Next.js Application)**

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js | 16.0.9 | React-based full-stack framework with App Router |
| **Language** | TypeScript | 5.8.3 | Type-safe JavaScript for reliability |
| **UI Library** | React | 19.2.0 | Component-based UI rendering |
| **Authentication** | NextAuth | 5.0.0-beta.30 | Healthcare staff authentication with role-based access |
| **Styling** | Tailwind CSS | 3.4.17 | Utility-first CSS framework |
| **Components** | shadcn/ui | Latest | Pre-built, accessible UI components |
| **Form Handling** | React Hook Form | 7.61.1 | Form validation and state management |
| **Validation** | Zod | 3.25.76 | Schema validation for forms and API responses |
| **State Management** | React Query | 5.83.0 | Server state synchronization and caching |
| **Icons** | Lucide React | 0.462.0 | Icon library |
| **Notifications** | Sonner | 1.7.4 | Toast notifications for alerts |
| **Date Handling** | date-fns | 3.6.0 | Date formatting and manipulation |
| **Hosting** | Vercel | N/A | Edge-optimized hosting with zero-config deployment |

#### **Backend (Dual-Agent AI System)**

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **CareFlow Pulse Agent** | Google ADK | 1.16.0+ | Medical reasoning agent with MCP toolbox integration |
| **CareFlow Caller Agent** | LangGraph | Latest | Voice interface agent with REACT architecture |
| **Language** | Python | 3.10-3.12 | Backend logic for both agents |
| **AI Model** | Gemini 3 Flash (Preview) | Latest | Fast, intelligent LLM for medical triage and conversation |
| **MCP Protocol** | toolbox-core | Latest | Model Context Protocol for Firestore database access |
| **A2A Protocol** | a2a-sdk | Latest | Agent-to-Agent communication (JSON-RPC + SSE) |
| **Voice Interface** | Twilio ConversationRelay | Latest | Real-time voice streaming with WebSocket |
| **Call Recording (v3.4)** | Twilio Recordings API | Latest | MP3 recordings for Gemini 3 audio analysis |
| **Text-to-Speech** | ElevenLabs | Latest | Natural-sounding voice synthesis (voice: UgBBYS2sOqTuMpoF3BR0) |
| **LangChain Integration** | langchain-google-genai | 2.0.7+ | LangChain + Gemini for caller agent |
| **Deployment** | Google Cloud Run | N/A | Containerized deployment (2 separate services) |
| **Container Registry** | Artifact Registry | N/A | Docker image storage |
| **Environment** | python-dotenv | Latest | Environment variable management |

#### **Database**

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Primary Database** | Google Cloud Firestore | NoSQL document database for patient data, interactions, alerts |
| **Real-Time Sync** | Firestore SDKs | WebSocket-based live updates to frontend |
| **Data Model** | Document/Collection | Hierarchical structure with sub-collections |

#### **External Services & APIs**

| Service | Provider | Purpose |
| :--- | :--- | :--- |
| **Voice Streaming** | Twilio ConversationRelay | Real-time voice conversation management with WebSocket |
| **Text-to-Speech** | ElevenLabs | Natural-sounding voice synthesis for patient interactions |
| **SMS Messaging** | Twilio SMS API | Send/receive text messages for medication reminders |
| **Database** | Google Cloud Firestore | NoSQL document database for patient data, interactions, alerts |
| **Container Hosting** | Google Cloud Run | Serverless container hosting for both agents |
| **Container Registry** | Google Cloud Artifact Registry | Docker image storage and management |
| **Monitoring** | Google Cloud Logging | Centralized logging and tracing |

#### **Development & DevOps**

| Tool | Purpose |
| :--- | :--- |
| **Makefile** | Development workflow orchestration (install, dev, deploy) |
| **Git** | Version control (GitHub repository) |
| **npm/bun** | Frontend package management |
| **uv** | Backend package management |
| **Environment Files** | `.env` for configuration management |

---

## **2.3. Component Interaction Flow**

This section describes the typical request flow through the system for key scenarios.

#### **Flow 1: Scheduled Patient Follow-Up Call**

```
1. Cloud Scheduler (8:15 AM)
   │
   ├─→ POST [Dispatcher Function] (Loops active hospitals)
   │   │
   │   └─→ POST https://careflow-agent-hospXXX.run.app/start
   │       Body: { "timeSlot": "morning", "hour": 8 }
   │
2. CareFlow-Main Agent (HOSPXXX Context)
   │
   ├─→ Query Firestore: Get patients with medications at 8am
   │   WHERE hospitalId == "HOSPXXX" AND dischargePlan.medications[].scheduleHour == 8
   │
3. For each patient:
   │
   ├─→ CareFlow-Connect Agent
   │   │
   │   ├─→ Generate Dynamic Prompt (patient context + safety rules)
   │   │
   │    ├─→ Twilio Voice API: Initiate call
    │       │
    │       └─→ Connect to Twilio ConversationRelay for streaming
    │           │
    │           └─→ ElevenLabs for real-time TTS synthesis
    │
4. Patient answers, conversation happens
    │
5. Twilio CR sends WebSocket events/final transcript
    │
    ├─→ POST /api/careflow/voice-alert
   │
6. CareFlow-Analyze Agent
   │
   ├─→ Analyze transcript for risk keywords
   │   • Check for critical symptoms
   │   • Assess medication adherence
   │
   ├─→ Classify Risk: GREEN / ORANGE / RED
   │
7. CareFlow-Main updates Firestore
   │
   ├─→ /patients/{id}
   │   • Update riskLevel
   │   • Create alert if RED/ORANGE
   │   • Log medication taken in /medicationLog
   │
   ├─→ /patients/{id}/interactions
   │   • Store full transcript
   │   • Save analysis result
   │
   └─→ /alerts (if RED/ORANGE)
       • Create new alert document
       • Status: "active"
       • Trigger: AI-generated reason
│
8. Firestore onSnapshot listeners
   │
   └─→ Next.js Dashboard updates in real-time
       • Patient card turns RED
       • Alert appears at top of list
       • Nurse receives notification
```

#### **Flow 2: Nurse Responds to Critical Alert**

```
1. Nurse Sarah sees RED alert on dashboard
   │
2. Clicks "View Patient" → /patient/{patientId}
   │
   ├─→ Next.js fetches from Firestore:
   │   • Patient document
   │   • Latest interactions sub-collection
   │   • Medication logs
   │   • AI brief
   │
3. Dashboard displays:
   │
   ├─→ Patient vitals & history
   ├─→ Full conversation transcript
   ├─→ AI risk analysis
   └─→ "Take Ownership" button
   │
4. Nurse clicks "Take Ownership"
   │
   ├─→ Next.js updates Firestore /alerts/{alertId}
   │   • assignedTo: "nurse_sarah_123"
   │   • assignedAt: NOW()
   │   • status: "in_progress"
   │
5. Nurse calls patient directly
   │
6. After resolution, nurse marks alert as resolved
   │
   └─→ Next.js updates Firestore
       • /alerts/{alertId}.status = "resolved"
       • /alerts/{alertId}.resolvedAt = NOW()
       │
       └─→ Create nurse note in /patients/{id}/interactions
           • type: "NURSE_NOTE"
           • content: { note, actionsTaken }
```

---

### **2.4. Deployment Architecture**

CareFlow Pulse is deployed across multiple Google Cloud and Vercel environments.

```
┌───────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                      │
└───────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │               VERCEL (Global Edge Network)               │
    │                                                            │
    │  • Next.js Frontend (SSR + Static)                        │
    │  • Automatic HTTPS                                        │
    │  • CDN for static assets                                  │
    │  • Environment: production                                │
    │  • Domain: app.careflow-pulse.com                         │
    └─────────────────────┬────────────────────────────────────┘
                          │
                          │ HTTPS
                          │
    ┌─────────────────────▼────────────────────────────────────┐
    │         GOOGLE CLOUD PLATFORM (us-central1)              │
    │                                                            │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │        Vertex AI Agent Engine                    │   │
    │  │  • ADK Multi-Agent System (Python)               │   │
    │  │  • Auto-scaling (0 to N instances)               │   │
    │  │  • Model: Gemini 3 Flash (Preview)              │   │
    │  │  • Endpoints:                                    │   │
    │  │    - /api/careflow/trigger-scheduled-calls       │   │
    │  │    - /api/careflow/twilio-sms                    │   │
    │  │    - /api/careflow/voice-alert                   │   │
    │  └──────────────────────────────────────────────────┘   │
    │                                                            │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │        Cloud Firestore (Multi-region)            │   │
    │  │  • 4 Collections + 2 Sub-collections             │   │
    │  │  • Automatic backups (daily)                     │   │
    │  │  • Real-time sync enabled                        │   │
    │  │  • Security rules enforced                       │   │
    │  └──────────────────────────────────────────────────┘   │
    │                                                            │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │        Cloud Scheduler                           │   │
    │  │  • Job 1: morning-calls (8:15 AM daily)          │   │
    │  │  • Job 2: noon-calls (12:15 PM daily)            │   │
    │  │  • Job 3: evening-calls (8:15 PM daily)          │   │
    │  │  • Timezone: America/New_York                    │   │
    │  └──────────────────────────────────────────────────┘   │
    │                                                            │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │        Cloud Storage (Staging Bucket)            │   │
    │  │  • Agent deployment artifacts                    │   │
    │  │  • Call recordings (if enabled)                  │   │
    │  └──────────────────────────────────────────────────┘   │
    │                                                            │
    │  ┌──────────────────────────────────────────────────┐   │
    │  │        Cloud Logging & Monitoring                │   │
    │  │  • Structured logs from agents                   │   │
    │  │  • OpenTelemetry traces                          │   │
    │  │  • Alerting rules                                │   │
    │  └──────────────────────────────────────────────────┘   │
    └────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────┐
    │              EXTERNAL SERVICES (Third-Party)              │
    │                                                            │
      ┌──────────────────┐         ┌──────────────────┐
    │  Twilio          │         │  ElevenLabs      │
    │  • Voice calls   │         │  • TTS synthesis │
    │  • Call record.  │         │  • Ultra-low     │
    │  • SMS gateway   │         │    latency       │
    │  • Conv. Relay   │         │                  │
    └──────────────────┘         └──────────────────┘
       │
    └────────────────────────────────────────────────────────────┘

**Environment Separation:**

| Environment | Purpose | Configuration |
| :--- | :--- | :--- |
| **Development** | Local development on developer machines | `.env.local` files, mock data |
| **Staging** | Pre-production testing with real integrations | Separate GCP project, staging Twilio numbers |
| **Production** | Live system serving real patients | Production GCP project, production Twilio numbers, strict security |

**Deployment Process:**

1. **Frontend**: Git push to `main` → Automatic Vercel deployment
2. **Backend**: `make deploy` → ADK packages and deploys to Vertex AI Agent Engine
3. **Database**: Firestore rules deployed via Firebase CLI or console
4. **Scheduler**: Configured via Google Cloud Console or Terraform

---

### **2.5. Audio-First Reporting Architecture**

> **Key Architectural Shift:** In v3.4, the system pivots from transcript-based analysis to audio-based analysis, leveraging Gemini 3's native multimodal capabilities for richer, more accurate clinical assessments.

#### **Rationale**

Previous versions relied on text transcripts from Twilio ConversationRelay. While functional, this approach had significant clinical limitations:

| Limitation | Clinical Impact |
| :--- | :--- |
| **Lost Vocal Cues** | Transcripts cannot convey distress, confusion, or pain in the patient's voice |
| **ASR Accuracy** | Automatic speech recognition can misinterpret medical terminology |
| **Processing Latency** | Transcription adds delay before clinical analysis |

#### **Architecture Overview**

With Gemini 3's multimodal capabilities, the Pulse Agent directly "listens" to raw audio recordings, enabling:

- **Emotional Detection:** Identify distress, confusion, or pain from vocal tone
- **Subtle Clinical Cues:** Breathing patterns, hesitations, urgency in speech
- **Verbatim Context:** Hear exactly what the patient said, eliminating ASR errors

#### **Data Flow**

1. **Caller Agent** initiates patient call with Twilio recording enabled
2. **Twilio** stores call recording (MP3 format) upon completion
3. **Caller Agent** sends `CallSid` reference to Pulse Agent via A2A protocol
4. **Pulse Agent** fetches audio recording using dedicated tooling
5. **Gemini 3** performs native multimodal analysis on audio content
6. **Alert Creation** includes `callSid` field for frontend audio playback
7. **Nurse Dashboard** displays alert with embedded audio player (lazy-loaded)

#### **Component Responsibilities**

| Component | v3.3 Behavior | v3.4 Behavior |
| :--- | :--- | :--- |
| **Caller Agent** | Streamed transcripts in real-time | Records calls; sends only `CallSid` on completion |
| **Pulse Agent** | Analyzed transcript text | Fetches raw audio; performs multimodal analysis |
| **Alert Schema** | Text-only trigger/brief | Includes `callSid` for audio playback |
| **Frontend** | N/A | Audio player with secure proxy route |

#### **Security Considerations**

- Audio recordings remain on Twilio infrastructure until fetched
- Frontend accesses audio via secure server-side proxy (credentials never exposed to client)
- Audio playback follows HIPAA audit requirements for call recordings

---

### **2.6. Missed Call Detection & Retry System (NEW v3.8)**

> **Key Feature:** v3.8 introduces a comprehensive system for detecting missed calls (no-answer, busy, failed), logging these events for audit compliance, alerting nurses, and automatically scheduling retry attempts via Google Cloud Tasks.

#### **Problem Statement**

When patients don't answer scheduled wellness calls, the previous system would silently fail, potentially missing critical health check-ins. This created:

- **Clinical Risk**: Unreachable patients might be experiencing emergencies
- **Audit Gaps**: No record of failed contact attempts for HIPAA compliance
- **Manual Burden**: Nurses had no visibility into which patients couldn't be reached

#### **Architecture Overview**

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MISSED CALL DETECTION & RETRY SYSTEM v3.8                 │
└─────────────────────────────────────────────────────────────────────────────┘

   ┌───────────────────────────────────────────────────────────────────────────┐
   │                           INITIAL CALL FLOW                               │
   └───────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
   │  Pulse Agent    │  A2A    │  Caller Agent   │  Twilio │    Patient      │
   │  (Orchestrator) │────────►│  (Voice)        │────────►│    Phone        │
   └─────────────────┘         └────────┬────────┘         └─────────────────┘
                                        │
                                        │ Status Callback
                                        │ (no-answer/busy/failed)
                                        ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                        FAILURE DETECTION FLOW                             │
   └───────────────────────────────────────────────────────────────────────────┘

                               ┌─────────────────┐
                               │     Twilio      │
                               │ status_callback │
                               └────────┬────────┘
                                        │ POST /call-status
                                        ▼
                               ┌─────────────────┐
                               │  Caller Agent   │
                               │                 │
                               │  1. Parse status│
                               │  2. Send A2A ───┼────────────┐
                               │  3. Schedule    │            │
                               │     Cloud Task  │            │
                               └────────┬────────┘            │
                                        │                     │ A2A: CALL_FAILED
            ┌───────────────────────────┘                     │
            │ Schedule Task (15 min delay)                    ▼
            ▼                                        ┌─────────────────┐
   ┌─────────────────┐                               │  Pulse Agent    │
   │   Cloud Tasks   │                               │                 │
   │   Queue:        │                               │ • Update risk   │
   │ patient-retries │                               │   → "warning"   │
   └────────┬────────┘                               │ • Log to        │
            │                                        │   /interactions │
            │ POST /retry-rounds (after 15 min)      │ • Create alert  │
            │                                        └────────┬────────┘
            ▼                                                 │
   ┌─────────────────┐                                        │ Write
   │  Pulse Agent    │                                        ▼
   │  /retry-rounds  │                               ┌─────────────────┐
   │                 │                               │   Firestore     │
   │ Check retryCount│                               │   Database      │
   │ If < 3:         │                               └─────────────────┘
   │  Send A2A to ───┼──► Caller Agent (new call)
   │  Caller Agent   │
   │ If >= 3:        │
   │  Create CRITICAL│
   │  alert          │
   └─────────────────┘

   ┌───────────────────────────────────────────────────────────────────────────┐
   │                           DASHBOARD UPDATE                                │
   └───────────────────────────────────────────────────────────────────────────┘

   Firestore ──────► onSnapshot listeners ──────► Next.js Dashboard
   (alerts/patients)                              • Warning badge
                                                  • Unreachable patient card
                                                  • Retry history
```

#### **Data Flow: Failed Call Handling**

```text
Step 1: Caller Agent initiates call via Twilio
        └──► Twilio calls patient phone

Step 2: Call fails (no-answer after 20s timeout)
        └──► Twilio sends POST to /call-status webhook

Step 3: Caller Agent receives status "no-answer"
        ├──► Sends A2A CALL_FAILED to Pulse Agent
        └──► Schedules Cloud Task (15 min delay)

Step 4: Pulse Agent processes CALL_FAILED message
        ├──► Updates patient riskLevel to "warning"
        ├──► Logs interaction in /patients/{id}/interactions
        └──► Creates alert with priority "warning"

Step 5: Dashboard updates in real-time
        └──► Nurse sees unreachable patient

Step 6: After 15 minutes, Cloud Tasks triggers /retry-rounds
        └──► Pulse Agent checks retryCount

Step 7: If retryCount < 3:
        ├──► Pulse Agent sends A2A to Caller Agent
        └──► Flow restarts at Step 1

Step 8: If retryCount >= 3:
        └──► Create CRITICAL alert, nurse must call manually
```

#### **Twilio Call Status Events**

The Caller Agent subscribes to all terminal Twilio call states:

| Event | Meaning | Action |
| :--- | :--- | :--- |
| `initiated` | Call request sent to carrier | Log start time |
| `ringing` | Phone is ringing | Monitor timeout |
| `answered` | Patient answered (human or machine) | Begin conversation |
| `completed` | Call ended normally | Send `CALL_COMPLETE` to Pulse Agent |
| `busy` | Line busy signal detected | Send `CALL_FAILED`, schedule retry |
| `no-answer` | No answer within timeout | Send `CALL_FAILED`, schedule retry |
| `failed` | Carrier/network failure | Send `CALL_FAILED`, create ORANGE alert |

**Configuration in Twilio API Call:**

```python
call = client.calls.create(
    to=patient_phone,
    from_=twilio_number,
    status_callback=f"{PUBLIC_URL}/call-status",
    status_callback_event=["initiated", "ringing", "answered", "completed", "busy", "failed", "no-answer"],
    status_callback_method="POST",
    machine_detection="Enable",
    async_amd="true",
    timeout=20  # Faster no-answer detection
)
```

#### **A2A Message Format: CALL_FAILED**

When a call fails, the Caller Agent sends this structured message to the Pulse Agent:

```text
CALL_FAILED: Patient [Patient Name] (ID: [patient_id]) is unreachable.
Call SID: [call_sid]
Status: [no-answer|busy|failed]
Schedule Slot: [2026-01-24_08]
Please log this failed interaction, update the patient's risk level to "warning",
and create an alert for the nursing staff.
```

#### **Retry Scheduling with Cloud Tasks**

When a call fails, the Caller Agent schedules a delayed retry using Google Cloud Tasks. Each retry is **patient-specific** with its own Cloud Task.

**How It Works:**

1. Patient A doesn't answer → Caller Agent creates Cloud Task for Patient A
2. Patient B is busy → Caller Agent creates Cloud Task for Patient B  
3. Each task executes independently after the delay

This **Individual Mode** approach ensures:

- No duplicate calls (each patient has exactly one pending retry)
- State travels with the task (no database needed for retry tracking)
- Clear audit trail per patient

**Cloud Task Configuration:**

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Queue Name** | `patient-retries` | Dedicated queue for patient contact retries |
| **Retry Delay** | 15 minutes | Balance between giving patient time and not waiting too long |
| **Max Attempts** | 3 | Prevent infinite retry loops |
| **Target Endpoint** | `POST /retry-rounds` | Pulse Agent handles retry orchestration |

**Task Payload Structure:**

| Field | Type | Description |
| :--- | :--- | :--- |
| `patientId` | string | The patient document ID to retry |
| `retryCount` | integer | Current attempt number (1, 2, or 3) |
| `scheduleSlot` | string | Original schedule slot (e.g., "2026-01-24_08") |
| `reason` | string | Why retry is needed (no-answer, busy, failed) |
| `scheduleHour` | integer | Hour of the schedule (8, 12, 20) |

#### **Retry Count Tracking (State in Payload)**

The `retryCount` is tracked **in the Cloud Task payload itself**, not in Firestore. This design:

- **Eliminates race conditions**: No concurrent writes to patient document
- **Self-contained**: Each retry chain carries its own state
- **Simpler queries**: No need to count failed interactions

**Lifecycle of retryCount:**

| Attempt | Action | Next retryCount |
| :--- | :--- | :--- |
| Initial call fails | Caller schedules task with `retryCount=1` | 1 |
| Retry #1 fails | Caller schedules task with `retryCount=2` | 2 |
| Retry #2 fails | Caller schedules task with `retryCount=3` | 3 |
| Retry #3 received | Pulse Agent sees `retryCount >= 3` → STOP | — |

#### **Max Retries Reached (retryCount >= 3)**

When the Pulse Agent receives a retry request with `retryCount >= 3`:

1. **No more automatic retries** are scheduled
2. **CRITICAL alert created** with:
   - `riskLevel: "RED"`
   - `priority: "critical"`
   - `trigger: "Patient unreachable after 3 attempts"`
3. **Patient record updated** with `riskLevel: "RED"`
4. **Nurse notification**: Alert appears immediately on dashboard

The nurse must then manually contact the patient.

#### **Component Responsibilities**

| Component | Responsibility |
| :--- | :--- |
| **Caller Agent** | Detects call failures, sends A2A notifications, schedules Cloud Tasks with `retryCount` |
| **Pulse Agent** | Receives retry triggers, checks `retryCount`, initiates patient calls or creates alerts |
| **Cloud Tasks** | Reliable delayed execution, automatic retry on HTTP failure |
| **Firestore** | Stores alerts and interactions (not retry state) |
| **Dashboard** | Real-time display of unreachable patients and critical alerts |

#### **New Files Introduced (v3.8)**

| File | Purpose |
| :--- | :--- |
| `caller-agent/app/app_utils/retry_utils.py` | Cloud Tasks scheduling utilities |
| `careflow-agent/app/tools/interaction_logger.py` | Firestore subcollection logging tool |
| `careflow-agent/app/tools/retry_tools.py` | Retry-related Firestore queries |
| `careflow-agent/app/app_utils/retry_utils.py` | Schedule slot key generation |

#### **Environment Variables**

| Variable | Example | Purpose |
| :--- | :--- | :--- |
| `CLOUD_TASKS_QUEUE` | `patient-retries` | Queue name for retry tasks |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Cloud Tasks region |
| `CAREFLOW_AGENT_URL` | `https://pulse.careflow.run.app` | Target URL for retry callbacks |

#### **Monitoring & Alerts**

Cloud Logging filters for retry system monitoring:

```text
resource.type="cloud_tasks_queue"
resource.labels.queue_id="patient-retries"
severity>=WARNING
```

**Key Metrics:**

- `cloudtasks.googleapis.com/queue/task_attempt_count` - Retry frequency
- `cloudtasks.googleapis.com/queue/task_attempt_latency` - Retry delays
- Custom: `careflow.patient.unreachable_count` - Patients with max retries

---

## **3. Database Design (Firestore)**

### **3.1. Overview & Design Principles**

CareFlow Pulse uses **Google Cloud Firestore** as its primary database. Firestore is a NoSQL, document-oriented database that provides:

- **Real-time synchronization** via WebSocket connections (`onSnapshot` listeners)
- **Scalability** to handle thousands of concurrent users
- **Offline support** for mobile applications (future enhancement)
- **Built-in security** through declarative security rules
- **Flexible schema** with nested documents and sub-collections

#### **Design Principles**

1. **Patient-Centric Model**: The `/patients` collection is the root entity; all other data relates to patients
2. **Sub-Collections for Scalability**: High-volume data (interactions, medication logs) are stored in sub-collections to avoid document size limits (1MB per document)
3. **Denormalization for Performance**: Active alerts are duplicated in a separate `/alerts` collection for fast dashboard queries
4. **Timestamp Everything**: All documents include `createdAt` and `updatedAt` timestamps for audit trails
5. **Indexed Fields**: Fields used in queries (e.g., `riskLevel`, `status`, `scheduleHour`) are indexed for performance
6. **Multi-Tenancy (Logical Isolation)**: Every top-level document (`/patients`, `/alerts`, `/users`) MUST ideally contain a `hospitalId` field. Queries are strictly scoped by this field to ensure data isolation.
   - **Agent Enforcement**: Agents are deployed with `HOSPITAL_ID` env var and refuse to query data without this filter.
   - **Frontend Enforcement**: UI components filter data based on the logged-in user's `hospitalId`.

#### **Database Structure Overview**

```

Firestore Root
│
├── /patients/{patientId}                    [Main patient records]
│   ├── /interactions/{interactionId}        [Sub-collection: Call logs, SMS, analysis]
│   └── /medicationLog/{logId}               [Sub-collection: Medication adherence tracking]
│
├── /alerts/{alertId}                        [Active alerts for dashboard]
│
└── /users/{userId}                          [Healthcare staff accounts]

```

---

### **3.2. Collection: `/patients`**

**Purpose:** Central repository for all patient information, including medical context, contact details, current risk status, and care team assignments.

**Document ID:** `{patientId}` - A UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`)

#### **Schema**

| Field | Type | Required | Description | Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `patientId` | `string` | ✅ | Unique identifier (matches document ID) | `"550e8400-e29b-41d4-a716-446655440000"` | UUID v4 format |
| `hospitalId` | `string` | ✅ | Tenant Identifier for Logical Isolation | `"HOSP001"` | **Indexed** for Multi-Tenancy |
| `name` | `string` | ✅ | Patient's full name | `"Sarah Mitchell"` | PHI - encrypted at rest |
| `dateOfBirth` | `Timestamp` | ✅ | Date of birth for age calculation | `Timestamp(1978-03-15)` | PHI |
| `contact` | `Map` | ✅ | Contact information object | See below | PHI |
| `dischargePlan` | `Map` | ✅ | Medical discharge context | See below | Critical for AI prompt generation |
| `riskLevel` | `string` | ✅ | Current patient risk classification | `"GREEN"` | Enum: `GREEN`, `ORANGE`, `RED` - **Indexed** |
| `lastAssessmentDate` | `Timestamp` | ✅ | When risk was last evaluated | `Timestamp(2025-11-15 08:20)` | Updated after each interaction |
| `alert` | `Map` or `null` | ⚠️ | Active alert object (null if no alert) | See below | Only present for ORANGE/RED patients |
| `assignedNurse` | `Map` | ✅ | Primary nurse coordinator | See below | For handover and notifications |
| `aiBrief` | `string` | ❌ | Latest AI-generated summary | `"Patient stable, no concerns"` | Generated by Pulse Agent during post-call analysis |
| `createdAt` | `Timestamp` | ✅ | Record creation timestamp | `Timestamp(2025-11-10 14:30)` | Immutable |
| `updatedAt` | `Timestamp` | ✅ | Last modification timestamp | `Timestamp(2025-11-15 08:20)` | Auto-updated on changes |
| `status` | `string` | ✅ | Patient monitoring status | `"active"` | Enum: `active`, `completed`, `transferred` |

#### **Nested Object: `contact`**

```typescript
contact: {
  phone: string;                // "+15551234567" (E.164 format)
  email?: string;               // "sarah.mitchell@email.com" (optional)
  preferredMethod: "voice" | "sms";  // Communication preference
}
```

#### **Nested Object: `dischargePlan`**

This object contains all medical context needed for AI prompt generation and risk assessment.

```typescript
dischargePlan: {
  dischargeDate: Timestamp;           // When patient was discharged
  diagnosis: string;                  // "Post-operative cardiac surgery (CABG)"
  primaryDiagnosisCode?: string;      // "I25.10" (ICD-10 code, optional)
  dischargingPhysician: string;       // "Dr. Emily Rodriguez"
  hospitalId: string;                 // "HOSP001"
  
  medications: Array<{
    name: string;                     // "Aspirin"
    dosage: string;                   // "81mg"
    frequency: string;                // "Once daily at 8:00 AM"
    scheduleHour: number;             // 8, 12, or 20 (for scheduler queries) - **Indexed**
    instructions?: string;            // "Take with food"
    startDate: Timestamp;             // When medication started
    endDate?: Timestamp;              // When to stop (null = ongoing)
  }>;
  
  criticalSymptoms: string[];         // ["chest pain", "shortness of breath", "dizziness"]
  warningSymptoms: string[];          // ["increased swelling", "persistent cough", "fatigue"]
}
```

**💡 Design Note:** The `scheduleHour` field (8, 12, or 20) allows efficient Firestore queries:

```javascript
// Query patients who need a call at 8:15 AM
db.collection('patients')
  .where('dischargePlan.medications', 'array-contains', { scheduleHour: 8 })
  .where('status', '==', 'active')
  .get();
```

#### **Nested Object: `alert`**

Only present when `riskLevel` is `ORANGE` or `RED`. Set to `null` for `GREEN` patients.

```typescript
alert: {
  isCritical: boolean;                // true for RED, false for ORANGE
  reason: string;                     // "Patient reports chest pain and dizziness"
  timestamp: Timestamp;               // When alert was generated
  assignedTo?: string;                // User ID of nurse who took ownership
  assignedAt?: Timestamp;             // When nurse claimed alert
  status: "active" | "in_progress" | "resolved";
} | null
```

#### **Nested Object: `assignedNurse`**

```typescript
assignedNurse: {
  userId: string;                     // "user_nurse_sarah_123"
  name: string;                       // "Sarah Johnson, RN"
  phone: string;                      // "+15559876543"
  email: string;                      // "sarah.johnson@hospital.com"
}
```

#### **Example Document**

```json
{
  "patientId": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Sarah Mitchell",
  "dateOfBirth": {"_seconds": 258249600, "_nanoseconds": 0},
  "contact": {
    "phone": "+15551234567",
    "email": "sarah.mitchell@email.com",
    "preferredMethod": "voice"
  },
  "dischargePlan": {
    "dischargeDate": {"_seconds": 1731196800, "_nanoseconds": 0},
    "diagnosis": "Post-operative cardiac surgery (CABG)",
    "primaryDiagnosisCode": "I25.10",
    "dischargingPhysician": "Dr. Emily Rodriguez",
    "hospitalId": "HOSP001",
    "medications": [
      {
        "name": "Aspirin",
        "dosage": "81mg",
        "frequency": "Once daily at 8:00 AM",
        "scheduleHour": 8,
        "instructions": "Take with food",
        "startDate": {"_seconds": 1731196800, "_nanoseconds": 0},
        "endDate": null
      },
      {
        "name": "Metoprolol",
        "dosage": "50mg",
        "frequency": "Twice daily at 8:00 AM and 8:00 PM",
        "scheduleHour": 8,
        "startDate": {"_seconds": 1731196800, "_nanoseconds": 0},
        "endDate": null
      }
    ],
    "criticalSymptoms": ["chest pain", "shortness of breath", "dizziness", "irregular heartbeat"],
    "warningSymptoms": ["increased swelling", "persistent fatigue", "mild chest discomfort"]
  },
  "riskLevel": "RED",
  "lastAssessmentDate": {"_seconds": 1731668400, "_nanoseconds": 0},
  "alert": {
    "isCritical": true,
    "reason": "Patient reports chest pain radiating to left arm and dizziness",
    "timestamp": {"_seconds": 1731668400, "_nanoseconds": 0},
    "assignedTo": "user_nurse_sarah_123",
    "assignedAt": {"_seconds": 1731668580, "_nanoseconds": 0},
    "status": "in_progress"
  },
  "assignedNurse": {
    "userId": "user_nurse_sarah_123",
    "name": "Sarah Johnson, RN",
    "phone": "+15559876543",
    "email": "sarah.johnson@hospital.com"
  },
  "aiBrief": "URGENT: Patient reports concerning cardiac symptoms consistent with post-CABG complications. Immediate assessment required.",
  "createdAt": {"_seconds": 1731196800, "_nanoseconds": 0},
  "updatedAt": {"_seconds": 1731668400, "_nanoseconds": 0},
  "status": "active"
}
```

---

### **3.3. Sub-Collection: `/patients/{patientId}/interactions`**

**Purpose:** Chronological, auditable log of every interaction with the patient—voice calls, SMS messages, AI analysis, status changes, and nurse notes.

**Document ID:** Auto-generated by Firestore (timestamped)

**Path:** `/patients/{patientId}/interactions/{interactionId}`

#### **Schema**

| Field | Type | Required | Description | Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `timestamp` | `Timestamp` | ✅ | When this interaction occurred | `Timestamp(2025-11-15 08:15:30)` | Primary sort key |
| `type` | `string` | ✅ | Type of interaction | `"OUTBOUND_CALL"` | See enum below |
| `content` | `Map` | ✅ | Type-specific content object | See below | Structure varies by type |
| `riskClassification` | `string` | ❌ | Risk level determined from this interaction | `"RED"` | Only for AGENT_ANALYSIS types |
| `aiBrief` | `string` | ❌ | AI-generated summary for critical events | `"Patient stable, medications taken on time"` | Only for RED/ORANGE events |
| `agentName` | `string` | ❌ | Which agent handled this | `"Pulse Agent"` | For audit trail and debugging |
| `processingTime` | `number` | ❌ | Processing duration in milliseconds | `1234` | Performance monitoring |

#### **Type Enum**

```typescript
type InteractionType = 
  | "OUTBOUND_CALL"      // Agent initiated a voice call to patient
  | "OUTBOUND_SMS"       // Agent sent an SMS to patient
  | "INBOUND_SMS"        // Patient replied via SMS
  | "AGENT_ANALYSIS"     // AI analyzed patient response and classified risk
  | "STATUS_CHANGE"      // Patient risk level changed (GREEN → RED, etc.)
  | "NURSE_NOTE"         // Nurse added a manual note
  | "SYSTEM_EVENT";      // System-level event (e.g., medication reminder)
```

#### **Content Object by Type**

**For `OUTBOUND_CALL`:**

```typescript
content: {
  message?: string;                   // Opening message from agent
  transcript: string;                 // Full conversation transcript
  duration: number;                   // Call duration in seconds
  callSid: string;                    // Twilio call identifier
  callStatus: "completed" | "no-answer" | "busy" | "failed";
  medicationChecked?: string[];       // Which medications were discussed
}
```

**For `OUTBOUND_SMS`:**

```typescript
content: {
  message: string;                    // SMS body sent to patient
  messageSid: string;                 // Twilio message identifier
  deliveryStatus: "sent" | "delivered" | "failed";
}
```

**For `INBOUND_SMS`:**

```typescript
content: {
  patientMessage: string;             // What patient texted back
  messageSid: string;                 // Twilio message identifier
  receivedAt: Timestamp;              // When SMS was received
}
```

**For `AGENT_ANALYSIS`:**

```typescript
content: {
  analysisResult: {
    previousRisk: "GREEN" | "ORANGE" | "RED";
    newRisk: "GREEN" | "ORANGE" | "RED";
    reasoning: string;                // AI explanation for classification
    keyFindings: string[];            // ["fever", "shortness of breath"]
    confidence: number;               // 0.0 to 1.0 (AI confidence score)
  };
}
```

**For `STATUS_CHANGE`:**

```typescript
content: {
  statusChange: {
    from: string;                     // "GREEN"
    to: string;                       // "RED"
    reason: string;                   // "Critical symptoms reported"
    triggeredBy: "ai_analysis" | "nurse_manual" | "system";
  };
}
```

**For `NURSE_NOTE`:**

```typescript
content: {
  nurseNote: {
    nurseId: string;                  // "user_nurse_sarah_123"
    nurseName: string;                // "Sarah Johnson, RN"
    note: string;                     // Free-text nurse notes
    actionsTaken: string[];           // ["Called patient", "Advised to go to ER"]
  };
}
```

**For `SYSTEM_EVENT`:**

```typescript
content: {
  eventType: string;                  // "medication_reminder_sent"
  eventDetails: string;               // "Reminder for evening Aspirin dose"
}
```

#### **Example Document**

```json
{
  "timestamp": {"_seconds": 1731668400, "_nanoseconds": 0},
  "type": "OUTBOUND_CALL",
  "content": {
    "message": "Good morning Sarah, this is CareFlow checking in on your recovery.",
    "transcript": "Agent: Good morning Sarah, this is CareFlow checking in...\nPatient: Hello, I'm not feeling well. I have chest pain...\nAgent: I understand. Can you describe the pain?...",
    "duration": 180,
    "callSid": "CA1234567890abcdef",
    "callStatus": "completed",
    "medicationChecked": ["Aspirin", "Metoprolol"]
  },
  "riskClassification": "RED",
  "aiBrief": "Patient reports chest pain radiating to left arm. Immediate intervention required.",
  "agentName": "Pulse Agent",
  "processingTime": 2345
}
```

---

### **3.4. Sub-Collection: `/patients/{patientId}/medicationLog`**

**Purpose:** Detailed tracking of each medication dose—whether taken, missed, or late—to monitor adherence and display on the nurse dashboard.

**Document ID:** Auto-generated by Firestore (timestamped)

**Path:** `/patients/{patientId}/medicationLog/{logId}`

#### **Schema**

| Field | Type | Required | Description | Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `medicationName` | `string` | ✅ | Name of the medication | `"Aspirin"` | Must match name in `dischargePlan.medications` |
| `dosage` | `string` | ✅ | Dosage amount | `"81mg"` | For display purposes |
| `scheduledTime` | `Timestamp` | ✅ | When patient should have taken it | `Timestamp(2025-11-15 08:00)` | Expected time |
| `takenTime` | `Timestamp` | ❌ | When patient actually took it | `Timestamp(2025-11-15 08:15)` | Null if not taken |
| `status` | `string` | ✅ | Adherence status | `"taken"` | Enum: `taken`, `missed`, `late`, `pending` |
| `reportedBy` | `string` | ✅ | How we know this | `"patient_voice"` | Enum: `patient_voice`, `patient_sms`, `nurse` |
| `interactionId` | `string` | ❌ | Link to interaction where confirmed | `"abc123"` | Reference to `/interactions/{id}` |
| `notes` | `string` | ❌ | Additional context | `"Patient said took it 15 minutes ago"` | Free text |
| `createdAt` | `Timestamp` | ✅ | When log entry was created | `Timestamp(2025-11-15 08:20)` | Auto-generated |

#### **Status Enum**

```typescript
type MedicationStatus = 
  | "taken"      // Patient confirmed they took it
  | "missed"     // Patient confirmed they did NOT take it
  | "late"       // Taken more than 1 hour after scheduled time
  | "pending";   // Not yet time to take / no confirmation yet
```

#### **Example Document**

```json
{
  "medicationName": "Aspirin",
  "dosage": "81mg",
  "scheduledTime": {"_seconds": 1731664800, "_nanoseconds": 0},
  "takenTime": {"_seconds": 1731665700, "_nanoseconds": 0},
  "status": "taken",
  "reportedBy": "patient_voice",
  "interactionId": "interaction_abc123xyz",
  "notes": "Patient confirmed took with breakfast",
  "createdAt": {"_seconds": 1731668400, "_nanoseconds": 0}
}
```

---

### **3.5. Collection: `/alerts`**

**Purpose:** Denormalized collection for fast dashboard queries. Contains only active ORANGE/RED alerts to optimize nurse interface performance.

**Document ID:** Auto-generated by Firestore

**Path:** `/alerts/{alertId}`

#### **Schema**

| Field | Type | Required | Description | Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `alertId` | `string` | ✅ | Unique alert identifier (matches doc ID) | `"alert_abc123"` | Auto-generated |
| `hospitalId` | `string` | ✅ | Tenant Identifier | `"HOSP001"` | **Indexed** |
| `patientId` | `string` | ✅ | Reference to patient | `"550e8400-e29b-41d4-a716-446655440000"` | **Indexed** |
| `patientName` | `string` | ✅ | Patient name (denormalized for speed) | `"Sarah Mitchell"` | Displayed in alert list |
| `riskLevel` | `string` | ✅ | Alert severity | `"RED"` | Enum: `ORANGE`, `RED` - **Indexed** |
| `trigger` | `string` | ✅ | Why alert was created | `"High fever and chest pain reported"` | Brief description |
| `aiBrief` | `string` | ✅ | AI-generated summary for nurse | `"Patient reports persistent fever..."` | Critical context |
| `status` | `string` | ✅ | Alert workflow state | `"active"` | Enum: `active`, `in_progress`, `resolved` - **Indexed** |
| `assignedTo` | `Map` | ❌ | Nurse who claimed alert | See below | Null if unclaimed |
| `createdAt` | `Timestamp` | ✅ | When alert was generated | `Timestamp(2025-11-15 08:20)` | Sort key for dashboard |
| `resolvedAt` | `Timestamp` | ❌ | When alert was resolved | `Timestamp(2025-11-15 09:45)` | Null if still active |
| `resolutionNote` | `string` | ❌ | How alert was resolved | `"Patient called, advised to visit ER"` | Free text |
| `callSid` | `string` | ❌ | Twilio Call SID for audio playback (v3.4) | `"CA123abc456..."` | Links to Twilio recording |
| `patientRef` | `DocumentReference` | ✅ | Link to full patient record | `ref('/patients/{id}')` | For deep linking |

#### **Nested Object: `assignedTo`**

```typescript
assignedTo: {
  userId: string;                     // "user_nurse_sarah_123"
  userName: string;                   // "Sarah Johnson, RN"
  assignedAt: Timestamp;              // When nurse clicked "Take Ownership"
} | null
```

#### **Example Document**

```json
{
  "alertId": "alert_550e8400abc",
  "patientId": "550e8400-e29b-41d4-a716-446655440000",
  "patientName": "Sarah Mitchell",
  "riskLevel": "RED",
  "trigger": "Chest pain radiating to left arm and dizziness",
  "aiBrief": "URGENT: Patient reports concerning cardiac symptoms consistent with post-CABG complications. Immediate assessment required. Patient is post-op day 5 from cardiac surgery.",
  "status": "in_progress",
  "assignedTo": {
    "userId": "user_nurse_sarah_123",
    "userName": "Sarah Johnson, RN",
    "assignedAt": {"_seconds": 1731668580, "_nanoseconds": 0}
  },
  "createdAt": {"_seconds": 1731668400, "_nanoseconds": 0},
  "resolvedAt": null,
  "resolutionNote": null,
  "patientRef": "/patients/550e8400-e29b-41d4-a716-446655440000"
}
```

**⚠️ Important:** When a patient's `riskLevel` changes to GREEN, the corresponding alert in `/alerts` should be marked as `resolved` or deleted to keep the dashboard clean.

---

### **3.6. Collection: `/users`**

**Purpose:** Healthcare staff accounts (nurses, coordinators, admins) with authentication details and preferences.

**Document ID:** `{userId}` - Matches NextAuth user ID

**Path:** `/users/{userId}`

#### **Schema**

| Field | Type | Required | Description | Example | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `userId` | `string` | ✅ | Unique user identifier (matches doc ID) | `"user_nurse_sarah_123"` | From NextAuth |
| `email` | `string` | ✅ | Login email | `"sarah.johnson@hospital.com"` | Unique, indexed |
| `name` | `string` | ✅ | Full name | `"Sarah Johnson, RN"` | Display name |
| `role` | `string` | ✅ | User role | `"nurse"` | Enum: `nurse`, `coordinator`, `admin` - **Indexed** |
| `licenseNumber` | `string` | ❌ | Professional license number | `"RN-12345-CA"` | Optional for admins |
| `department` | `string` | ❌ | Hospital department | `"Cardiology"` | For filtering |
| `hospitalId` | `string` | ✅ | Hospital/organization ID | `"HOSP001"` | Multi-tenancy support |
| `phone` | `string` | ✅ | Contact phone | `"+15559876543"` | For agent to call nurse |
| `assignedPatientIds` | `Array<string>` | ✅ | List of patient IDs | `["patient1", "patient2"]` | For filtering dashboard |
| `preferences` | `Map` | ✅ | User preferences | See below | Notification settings |
| `createdAt` | `Timestamp` | ✅ | Account creation date | `Timestamp(2025-10-01)` | Immutable |
| `lastLoginAt` | `Timestamp` | ✅ | Last login timestamp | `Timestamp(2025-11-15 07:30)` | Updated on auth |
| `isActive` | `boolean` | ✅ | Account status | `true` | For deactivation |

#### **Nested Object: `preferences`**

```typescript
preferences: {
  notificationMethod: "sms" | "email" | "both";  // How to send alerts
  alertSound: boolean;                           // Play sound for RED alerts
  timezone: string;                              // "America/New_York" (IANA format)
}
```

#### **Example Document**

```json
{
  "userId": "user_nurse_sarah_123",
  "email": "sarah.johnson@hospital.com",
  "name": "Sarah Johnson, RN",
  "role": "nurse",
  "licenseNumber": "RN-12345-CA",
  "department": "Cardiology",
  "hospitalId": "HOSP001",
  "phone": "+15559876543",
  "assignedPatientIds": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e9500-f39c-52e5-b827-557766551111"
  ],
  "preferences": {
    "notificationMethod": "both",
    "alertSound": true,
    "timezone": "America/New_York"
  },
  "createdAt": {"_seconds": 1727740800, "_nanoseconds": 0},
  "lastLoginAt": {"_seconds": 1731664200, "_nanoseconds": 0},
  "isActive": true
}
```

---

### **3.7. Indexes & Query Optimization**

To ensure fast query performance, the following Firestore composite indexes are required:

#### **Required Indexes**

```javascript
// Index 1: Active patients with medications at specific hour
Collection: patients
Fields:
  - status (Ascending)
  - dischargePlan.medications.scheduleHour (Ascending)
Query scope: Collection

// Index 2: Alerts by status and creation time
Collection: alerts
Fields:
  - status (Ascending)
  - createdAt (Descending)
Query scope: Collection

// Index 3: Alerts by risk level and status
Collection: alerts
Fields:
  - riskLevel (Ascending)
  - status (Ascending)
  - createdAt (Descending)
Query scope: Collection

// Index 4: Patients by risk level for dashboard
Collection: patients
Fields:
  - riskLevel (Ascending)
  - updatedAt (Descending)
Query scope: Collection

// Index 5: Users by hospital and role
Collection: users
Fields:
  - hospitalId (Ascending)
  - role (Ascending)
Query scope: Collection
```

**💡 Pro Tip:** Firestore will automatically suggest creating these indexes when you run queries during development. You can create them via the Firebase Console or deploy them using the Firebase CLI with an `firestore.indexes.json` file.

---

### **3.8. Security Rules**

Firestore security rules enforce access control at the database level. Below is a high-level overview; full rules are in **Appendix C**.

#### **Key Principles**

1. **Authentication Required**: All reads/writes require valid NextAuth session
2. **Role-Based Access**: Nurses can only access their assigned patients
3. **PHI Protection**: Sensitive fields like `contact.phone` are restricted
4. **Write Restrictions**: Patients collection is read-only from frontend (only agents can write)
5. **Audit Trail**: Interactions sub-collection is append-only (no deletes)

#### **Security Rule Snippet Example**

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper function: Check if user is authenticated
    function isAuthenticated() {
      return request.auth != null;
    }
    
    // Helper function: Check if user is a nurse
    function isNurse() {
      return isAuthenticated() && 
             get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'nurse';
    }
    
    // Patients collection
    match /patients/{patientId} {
      // Nurses can read their assigned patients
      allow read: if isNurse() && 
                     request.auth.uid in resource.data.assignedNurse.userId;
      
      // Only backend agents can write (via service account)
      allow write: if false; // Frontend cannot modify
    }
    
    // Alerts collection
    match /alerts/{alertId} {
      // All authenticated users can read alerts
      allow read: if isAuthenticated();
      
      // Nurses can update to claim alerts
      allow update: if isNurse() && 
                       request.resource.data.assignedTo.userId == request.auth.uid;
    }
    
    // ... (Full rules in Appendix C)
  }
}
```

---

## **4. Backend: AI Agent System (Google ADK)**

### **4.1. Agent Architecture Overview**

The backend of CareFlow Pulse is built using **Google's Agent Development Kit (ADK)**, a Python framework for creating multi-agent AI systems. The agents are deployed to **Vertex AI Agent Engine**, a fully managed, serverless platform that handles scaling, monitoring, and execution.

#### **Why Multi-Agent Architecture?**

Rather than using a single monolithic AI agent, CareFlow Pulse employs a **specialized agent pattern** where each agent has a focused responsibility:

- **Modularity**: Each agent can be developed, tested, and optimized independently
- **Maintainability**: Clear separation of concerns makes debugging easier
- **Scalability**: Agents can be scaled independently based on load
- **Prompt Optimization**: Each agent has a tailored system prompt for its specific task

#### **Agent Hierarchy**

```
┌─────────────────────────────────────────────────────────────┐
│                    Pulse Agent (Orchestrator)               │
│                    • Medical Intelligence (ADK)             │
│                    • MCP Toolbox Integration                │
└───────────┬───────────────────────────────────────────┬─────┘
            │                                           │
            │ A2A Protocol (JSON-RPC)                   │
            ▼                                           ▼
┌───────────────────────────┐           ┌───────────────────────────┐
│       Caller Agent        │           │     (Future Agents)       │
│  • Voice Interface (Twilio)│           │  • EHR Connector          │
│  • ElevenLabs TTS         │           │  • Patient Mobile App     │
└───────────────────────────┘           └───────────────────────────┘
```

#### **Deployment Platform: Google Cloud Run (The Fleet)**

All agents are packaged and deployed as **Stateless Services** on Google Cloud Run. To strictly enforce Multi-Tenancy:

- **Replication**: We deploy **One Agent Service per Hospital**.
- **Isolation**: Each service has a specific `HOSPITAL_ID` environment variable (e.g., `HOSP001`).
- **Logic**: The agent reads this variable at startup and strictly filters all Firestore queries by this ID.
- **Discovery**: The "Dispatcher" knows the URL of each hospital's agent service.

**Deployment Command:**

```bash
# Deploy for Hospital 1
gcloud run deploy careflow-agent-hosp001 \
  --image gcr.io/project/agent \
  --set-env-vars HOSPITAL_ID=HOSP001,FIREBASE_PROJECT_ID=...

# Deploy for Hospital 2
gcloud run deploy careflow-agent-hosp002 \
  --image gcr.io/project/agent \
  --set-env-vars HOSPITAL_ID=HOSP002,FIREBASE_PROJECT_ID=...
```

This strategy ensures that `HOSP001` agent **physically cannot** access `HOSP002` data due to logic and potential future IAM bindings.

---

### **4.2. Pulse Agent (Orchestrator & Intelligence)**

**Role:** The Pulse Agent is the "brain" of CareFlow. Built with Google ADK, it orchestrates patient rounds, performs clinical analysis, and manages all Firestore operations via MCP protocol.

**File:** `careflow-agents/careflow-agent/app/agent.py`

#### **Agent Architecture**

The Pulse Agent uses a **BaseAgent wrapper pattern** for enhanced control:

| Component | Implementation | Purpose |
| :--- | :--- | :--- |
| **CareFlowAgent** | Extends `BaseAgent` | Custom wrapper for execution control |
| **Internal LlmAgent** | `assistant` field | Handles LLM-based reasoning |
| **BuiltInPlanner** | With `include_thoughts=True` | Multi-step reasoning with thinking enabled |
| **audio_handoff_callback** | `after_tool_callback` | Injects audio into Gemini multimodal context |

#### **5 Core Workflows**

The Pulse Agent responds to different message types with distinct workflows:

| # | Workflow | Trigger | Actions |
| :--- | :--- | :--- | :--- |
| **1** | **Trigger Rounds** | "start daily rounds for [TIME]" | Query patients via MCP, send Rich Patient Brief to Caller Agent via A2A |
| **2** | **Audio-First Analysis** | "CALL_COMPLETE: [CallSid]" | Fetch audio via `fetch_call_audio`, analyze with Gemini multimodal, classify risk |
| **3** | **Text Summary Processing** | "Interview Summary" message | Parse text report, apply risk classification, create alerts if needed |
| **4** | **Answer Caller Questions** | Questions from Caller Agent | Look up patient data in Firestore, provide clinical context |
| **5** | **Inbound Call Handling** | Patient lookup request | Search patient by name, return full context to Caller Agent |

> **Critical Rule:** The agent only modifies the database on receipt of actionable triggers (Workflows 1-3). All other messages are handled as informational queries to prevent duplicate alerts.

#### **Tools & Integrations**

| Category | Tools | Purpose |
| :--- | :--- | :--- |
| **MCP Toolbox** | `get_patients_for_schedule`, `create_alert`, `update_patient_risk`, `log_patient_interaction` | Firestore CRUD operations via MCP protocol |
| **A2A Protocol** | `list_remote_agents`, `send_remote_agent_task` | Inter-agent communication with Caller Agent |
| **Audio Fetch** | `fetch_call_audio` | Retrieve Twilio call recordings for multimodal analysis |

#### **Responsibilities**

| Responsibility | Description |
| :--- | :--- |
| **Webhook Handling** | Receives POST requests from Cloud Scheduler and Twilio |
| **Request Routing** | Determines which workflow to execute based on message content |
| **Audio Analysis (v3.4)** | Fetches raw call audio and performs Gemini 3 multimodal analysis |
| **Firestore Sync** | All database reads/writes via MCP Toolbox |
| **Alert Generation** | Creates alerts for Yellow/Red risk classifications |
| **Hospital Scoping** | All queries filtered by `HOSPITAL_ID` for multi-tenant isolation |

---

### **4.3. Caller Agent (Voice & Messaging Interface)**

**Role:** The Caller Agent (LangGraph-based) serves as the "voice" of the system, handling both outbound wellness check-ins and inbound patient calls. It connects to Twilio ConversationRelay for natural, real-time voice conversations with patients.

**File:** `careflow-agents/caller-agent/app/agent.py`

#### **Dual Mode Operation**

The Caller Agent operates in two distinct modes:

| Mode | Trigger | Workflow |
| :--- | :--- | :--- |
| **Outbound** | A2A task from Pulse Agent with "Rich Patient Brief" | Conducts structured AHRQ RED interview |
| **Inbound** | Patient calls the CareFlow number directly | Identifies patient, retrieves context, assists |

#### **AHRQ RED Interview Protocol (Outbound)**

For outbound calls, the Caller Agent follows the **AHRQ RED Tool 5 Post-Discharge Call** protocol with five structured phases. (See Functional Specs Section 1.4 for full AHRQ RED documentation.)

| Phase | Objective | Key Actions |
| :--- | :--- | :--- |
| **1. Cognitive Alignment** | Verify patient understands their diagnosis | Teach-back methodology |
| **2. Medication Audit** | Confirm safe medication management | Verify name, dose, purpose of each high-alert med |
| **3. Barrier Identification** | Detect obstacles to follow-up care | Transportation, financial, caregiver availability |
| **4. Home Services Validation** | Confirm equipment delivery and setup | Verify patient comfort with home services |
| **5. Safety Net Stress Test** | Validate emergency response plan | Quiz patient on red flag symptoms |

#### **Responsibilities**

| Responsibility | Description | Output |
| :--- | :--- | :--- |
| **Dynamic Prompt Generation** | Creates context-rich prompt for each patient from "Rich Patient Brief" | Conversation context |
| **Call Initiation** | Triggers Twilio Voice API with `record=true` | Twilio Call SID |
| **Call Recording (v3.4)** | All calls recorded; `CallSid` sent to Pulse Agent on completion | Audio reference |
| **Patient Lookup (Inbound)** | Queries Pulse Agent via A2A to identify caller | Patient context |
| **SMS Fallback** | Sends text messages when voice is unavailable | Twilio Message SID |

#### **Security Integration**

All agent inputs and outputs pass through **Model Armor** for security validation. See Section 9.3 for details on prompt injection defense and PHI redaction.

#### **External Integrations**

| Integration | Purpose |
| :--- | :--- |
| **Twilio ConversationRelay** | Real-time voice streaming with WebSocket |
| **ElevenLabs TTS** | Ultra-realistic medical persona voice synthesis |
| **A2A Protocol** | Inter-agent communication with Pulse Agent |

---

### **4.4. Clinical Reasoning: Triage & Analysis**

**Role:** A core competency of the **Pulse Agent**. It analyzes interaction data (transcripts, telemetry) to quantify clinical risk.

**File:** `app/agent.py` (specialized agent)

#### **Responsibilities**

| Responsibility | Description | Output |
| :--- | :--- | :--- |
| **Symptom Analysis** | Parses patient's words for medical keywords | Key findings list |
| **Risk Classification** | Assigns `GREEN`, `ORANGE`, or `RED` based on severity | Risk level enum |
| **Reasoning Generation** | Explains WHY the classification was chosen | String (reasoning) |
| **Medication Adherence** | Determines if patient took medications on time | Boolean + timestamp |
| **Alert Creation Logic** | Decides if nurse should be notified | Boolean (create alert?) |

#### **Analysis Prompt Structure**

The CareFlow-Analyze agent receives the conversation transcript and must perform risk assessment using a structured prompt that includes:

**Required Context:**

- Patient diagnosis and days since discharge
- Critical symptoms list from Firestore
- Warning symptoms list from Firestore
- Full conversation transcript

**Risk Classification Criteria:**

**🔴 RED (Critical - Immediate Action Required):**

- Patient mentions ANY symptom from criticalSymptoms list
- Severe pain reported (8-10/10 scale)
- Signs of infection (high fever >101°F, confusion, severe swelling)
- Medication adverse reaction
- Patient sounds distressed or in immediate danger

**🟠 ORANGE (Warning - Close Monitoring Needed):**

- Patient mentions symptoms from warningSymptoms list
- Moderate pain (5-7/10 scale)
- Missed multiple medication doses
- Vague concerns that aren't immediately critical
- Patient sounds uncertain about recovery progress

**🟢 GREEN (Safe - Routine Monitoring):**

- No concerning symptoms mentioned
- Medications taken as scheduled
- Positive recovery indicators
- Patient sounds confident and comfortable

**Required Output Structure (JSON):**

- `riskLevel`: String enum (GREEN/ORANGE/RED)
- `keyFindings`: Array of symptom keywords found
- `reasoning`: Brief explanation (1-2 sentences)
- `medicationAdherence`: Boolean
- `recommendedAction`: Action for nurse (if not GREEN)
- `confidence`: Float (0.0 to 1.0)

#### **Example Analysis Output**

**Input Transcript:**

```
Agent: Good morning Sarah, how are you feeling today?
Patient: Not great. I have a lot of chest pain, and I'm feeling dizzy.
Agent: Can you describe the chest pain?
Patient: It's like pressure, and it goes down my left arm.
```

**Analysis Output:**

```json
{
  "riskLevel": "RED",
  "keyFindings": ["chest pain", "dizziness", "pain radiating to left arm"],
  "reasoning": "Patient reports classic cardiac symptoms (chest pain with left arm radiation) combined with dizziness. This is extremely concerning for a post-CABG patient and requires immediate evaluation.",
  "medicationAdherence": null,
  "recommendedAction": "Call patient immediately. Consider advising ER visit or calling EMS.",
  "confidence": 0.98
}
```

#### **Post-Analysis Actions by Risk Level**

Based on the risk classification, the orchestrator must execute different workflows:

**For RED Alerts:**

1. Update `/patients/{id}`: Set `riskLevel` to RED, update `lastAssessmentDate`, populate `alert` object with critical flag
2. Create document in `/alerts` collection with patient details and AI brief
3. Log interaction in `/patients/{id}/interactions` with type `AGENT_ANALYSIS`
4. Generate detailed clinical summary (AI Brief)
5. Initiate voice call to assigned nurse with critical alert message
6. If nurse doesn't answer, send SMS alert as fallback

**For ORANGE Alerts:**

1. Update `/patients/{id}`: Set `riskLevel` to ORANGE, populate `alert` object (non-critical flag)
2. Create document in `/alerts` collection
3. Log interaction in sub-collection
4. Dashboard notification only (no immediate call to nurse)

**For GREEN Status:**

1. Update `/patients/{id}`: Set `riskLevel` to GREEN, clear `alert` field (set to null)
2. Log interaction in sub-collection
3. Update `/medicationLog` if medications were confirmed taken
4. No alert creation, no nurse notification

---

### **4.5. Clinical Reasoning: Medical Synthesis**

**Role:** Generates concise, actionable summaries for nurses when a RED or ORANGE alert is triggered.

**File:** `app/agent.py` (specialized agent)

#### **Responsibilities**

| Responsibility | Description | Output |
| :--- | :--- | :--- |
| **Context Aggregation** | Reads patient's full interaction history | List of interactions |
| **Summarization** | Condenses transcript into 2-3 key sentences | String (brief) |
| **Clinical Context** | Highlights relevant medical history | Part of brief |
| **Action Recommendations** | Suggests next steps for the nurse | Part of brief |
| **Urgency Emphasis** | Uses clear language for critical situations | Formatting |

#### **Brief Generation Requirements**

The CareFlow-Brief agent must create a concise clinical summary (2-3 sentences) for nurse coordinators that includes:

**Required Elements:**

1. **WHAT**: Patient's reported symptoms (from transcript)
2. **WHY**: Clinical context explaining why it's concerning given their diagnosis and post-discharge timeline
3. **ACTION**: Specific recommended next steps for the nurse

**Formatting Requirements:**

- Start with "URGENT:" prefix for RED alerts
- Use appropriate medical terminology
- Professional but urgent tone
- Maximum 3 sentences
- Specific and actionable

**Input Data Needed:**

- Patient name and diagnosis
- Days since discharge
- Full conversation transcript
- AI risk analysis results (risk level, key findings)

**Output Storage:**

- Store in `/patients/{id}.aiBrief` field
- Store in `/alerts/{id}.aiBrief` field
- Display on nurse dashboard

#### **Example Output**

**Brief for Dashboard:**

```
URGENT: Patient reports severe chest pain with left arm radiation and dizziness 
during morning check-in. Post-CABG day 5 patient exhibiting classic signs of 
potential cardiac event. IMMEDIATE ACTION REQUIRED: Call patient now and consider 
ER referral or EMS dispatch.
```

This brief is stored in:

- `/patients/{patientId}.aiBrief`
- `/alerts/{alertId}.aiBrief`

And displayed prominently on the nurse dashboard.

---

### **4.6. ADK Tools & Integrations**

ADK agents interact with external systems through **tools**—Python functions that the agents can "call" to perform actions.

#### **Tool 1: `mcp_firestore_toolbox`**

**Purpose:** Secure, governed access to Firestore via the Model Context Protocol (MCP).

**Capabilities:**

- `get_patient_risk`: Retrieves isolated patient risk context.
- `create_alert`: Generates documented nurse alerts.
- `update_patient_risk`: Updates clinical risk status.
- `log_interaction`: Appends to the auditable interaction history.

**Authentication:** Uses Google Cloud service account credentials configured in ADK deployment

#### **Tool 2: `a2a_caller_client`**

**Purpose:** Hand off voice session execution to the Caller Agent.

**Parameters:**

- `patient_id`: Target recipient.
- `clinical_context`: Dynamic context derived from Firestore.
- `callback_url`: Endpoint for session result delivery.

---

### **4.7. Prompt Engineering Strategy**

Effective prompts are critical for healthcare AI. Here are the principles used in CareFlow Pulse:

#### **Principles**

1. **Context-Rich**: Include patient name, diagnosis, medications, symptoms to watch
2. **Safety-First**: Explicit rules about when to escalate, never give medical advice
3. **Structured Output**: Request JSON format for parsing (risk classification)
4. **Examples**: Provide few-shot examples for complex tasks
5. **Guardrails**: Define boundaries (e.g., "If patient asks X, respond with Y")

#### **Prompt Template Structure**

All agent prompts should follow this consistent structure:

**1. Role Definition**: Define agent identity and expertise  
**2. Patient Context**: Include name, diagnosis, medications, symptoms to monitor  
**3. Task Definition**: Clear explanation of what agent must accomplish  
**4. Safety Rules**: Explicit boundaries (never give medical advice, when to escalate)  
**5. Output Format**: Specify structure (JSON, plain text, specific fields required)  
**6. Examples** (optional): Few-shot examples for complex classification tasks  
**7. Execution Trigger**: Clear instruction to begin processing  

#### **Prompt Versioning Strategy**

**Version Control:**

- All prompts must be version-controlled in Git
- Each prompt file should include version number (semantic versioning: X.Y.Z)
- Include changelog documenting what changed and why

**Versioning Format:**

- Major version (X): Breaking changes in output format or behavior
- Minor version (Y): New features or refined criteria
- Patch version (Z): Bug fixes or minor wording improvements

**Testing Requirement:** Any prompt version change must be tested with at least 10 sample patient scenarios before deployment

---

### **4.8. Error Handling & Fallback Logic**

Healthcare systems require robust error handling. CareFlow Pulse implements multiple layers of safety:

#### **Error Types & Responses**

| Error Type | Detection | Fallback Action |
| :--- | :--- | :--- |
| **Twilio Call Failed** | Status callback with `failed` | Retry once, then send SMS, log to Firestore |
| **Patient No Answer** | Status callback with `no-answer` | Create interaction log, schedule retry in 2 hours |
| **Deepgram Timeout** | No webhook received after 5 minutes | Mark call as `incomplete`, notify nurse |
| **AI Analysis Error** | Exception in CareFlow-Analyze | Default to ORANGE alert, log error, notify admin |
| **Firestore Write Failure** | SDK exception | Retry 3 times with exponential backoff, alert DevOps |
| **Invalid Patient Data** | Schema validation fails | Skip patient, log error, continue with others |

#### **Retry Logic Specification**

**For Firestore Operations:**

- Implement exponential backoff retry
- Maximum 3 retry attempts
- Wait time: 2 seconds, then 4 seconds, then 8 seconds
- Log each retry attempt with error details
- After 3 failures, escalate to DevOps alert

**For Twilio API Calls:**

- Retry once immediately for network errors
- Do not retry for invalid number errors (4xx status codes)
- Log failure reason to Firestore interaction log
- Fall back to SMS if voice call fails

#### **Circuit Breaker Pattern**

Implement circuit breaker for external service dependencies (Twilio, Deepgram) to prevent cascading failures:

**Circuit States:**

- **Closed (Normal)**: All requests flow through
- **Open (Failure)**: No requests sent, immediate fallback after 5 consecutive failures
- **Half-Open (Testing)**: After 60 seconds, allow 1 test request

**Fallback Actions:**

- Twilio voice failure → Send SMS instead
- Deepgram failure → Log error, create ORANGE alert for manual nurse follow-up
- Firestore failure → Queue write operations, retry when connection restored

#### **4.9. Native Multi-Language Support**

CareFlow Pulse leverages the native multilingual capabilities of the Gemini model family. The system can conduct interviews and perform clinical analysis in any language supported by Gemini, including but not limited to:
- English, Spanish, French, German
- Mandarin (Traditional/Simplified), Japanese, Korean
- Arabic, Hindi, Portuguese

The ElevenLabs voice integration uses the `eleven_multilingual_v2` model, ensuring natural-sounding speech across all supported locales.

---

## **5. Backend: API Endpoints**

### **5.1. Endpoint Overview**

The ADK backend deployed on Vertex AI Agent Engine exposes REST API endpoints for external triggers. These endpoints receive webhooks from Google Cloud Scheduler, Twilio, and Deepgram.

**Base URL (Production):** `https://agent-engine-{project-id}.{region}.run.app`  
**Base URL (Example):** `https://agent-engine-careflow.us-central1.run.app`

**Authentication:** All endpoints require Google Cloud IAM authentication OR API key configured in Cloud Scheduler / Twilio webhooks.

**Content-Type:** `application/json`

**Endpoint Summary:**

| Endpoint | Method | Trigger Source | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/careflow/trigger-scheduled-calls` | POST | Google Cloud Scheduler | Initiate scheduled patient follow-ups |
| `/api/careflow/twilio-sms` | POST | Twilio Webhook | Handle incoming SMS from patients |
| `/api/careflow/voice-alert` | POST | Deepgram/Twilio Webhook | Process completed voice call results |

---

### **5.2. `POST /api/careflow/trigger-scheduled-calls`**

**Purpose:** Triggered by Google Cloud Scheduler at 8:15 AM, 12:15 PM, and 8:15 PM daily to initiate patient follow-up calls for medication check-ins.

#### **Request Specification**

**HTTP Method:** `POST`

**Headers:**

- `Content-Type: application/json`
- `Authorization: Bearer {GOOGLE_CLOUD_TOKEN}` (for Cloud Scheduler authentication)

**Request Body Schema:**

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `timeSlot` | `string` | ✅ | Time of day identifier | `"morning"`, `"noon"`, `"evening"` |
| `hour` | `number` | ✅ | Hour for medication schedule filtering | `8`, `12`, `20` |
| `dryRun` | `boolean` | ❌ | If true, simulate without actually calling patients | `false` (default) |

**Example Request:**

```json
POST /api/careflow/trigger-scheduled-calls
Content-Type: application/json

{
  "timeSlot": "morning",
  "hour": 8,
  "dryRun": false
}
```

#### **Processing Logic**

1. **Query Firestore** for active patients:
   - Filter: `status == "active"`
   - Filter: `dischargePlan.medications[]` contains at least one med with `scheduleHour == {hour}`

2. **For each patient:**
   - Retrieve full patient document from Firestore
   - Delegate voice session to **Caller Agent** via A2A protocol
   - Provide clinical context (medications, symptoms) in the A2A task
   - Log outbound call initiation in `/patients/{id}/interactions`

3. **Handle Exceptions:**
   - Invalid patient phone number → Log error, skip patient, continue with others
   - Twilio API failure → Log error, send SMS fallback, continue
   - Firestore read error → Retry 3 times, then abort entire batch and alert DevOps

#### **Response Specification**

**Success Response (200 OK):**

| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | `string` | `"success"` |
| `patientsProcessed` | `number` | Count of patients who were called |
| `callsInitiated` | `number` | Count of successful Twilio calls started |
| `errors` | `array` | List of any non-critical errors encountered |
| `timestamp` | `string` | ISO 8601 timestamp of processing |

**Example Success Response:**

```json
{
  "status": "success",
  "patientsProcessed": 15,
  "callsInitiated": 14,
  "errors": [
    {
      "patientId": "patient-123",
      "error": "Invalid phone number",
      "action": "Skipped, logged for manual review"
    }
  ],
  "timestamp": "2025-11-15T08:15:30.123Z"
}
```

**Error Response (500 Internal Server Error):**

```json
{
  "status": "error",
  "message": "Firestore connection failed after 3 retries",
  "timestamp": "2025-11-15T08:15:30.123Z"
}
```

#### **Idempotency**

This endpoint is **not idempotent**. Each invocation will trigger new calls to patients. Cloud Scheduler should be configured to call this endpoint **only once per scheduled time**.

#### **Rate Limiting**

No explicit rate limiting required (controlled by Cloud Scheduler frequency).

---

### **5.3. `POST /api/careflow/twilio-sms`**

**Purpose:** Webhook endpoint for Twilio to POST incoming SMS messages from patients. Processes patient replies and updates Firestore.

#### **Request Specification**

**HTTP Method:** `POST`

**Headers:**

- `Content-Type: application/x-www-form-urlencoded` (Twilio default)
- `X-Twilio-Signature: {signature}` (for webhook validation)

**Request Body (URL-encoded form data):**

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `From` | `string` | Patient's phone number | `"+15551234567"` |
| `To` | `string` | Twilio phone number | `"+15559876543"` |
| `Body` | `string` | SMS message text | `"YES I took my medication"` |
| `MessageSid` | `string` | Twilio message identifier | `"SM1234567890abcdef"` |
| `AccountSid` | `string` | Twilio account ID | `"AC1234567890abcdef"` |

**Example Request (URL-encoded):**

```
From=%2B15551234567&To=%2B15559876543&Body=YES+I+took+my+medication&MessageSid=SM1234567890abcdef
```

#### **Processing Logic**

1. **Validate Twilio Signature:**
   - Use Twilio Auth Token to verify `X-Twilio-Signature` header
   - Reject request if signature invalid (prevents spoofing)

2. **Identify Patient:**
   - Query Firestore `/patients` where `contact.phone == {From}`
   - If not found, send generic "Thank you" SMS and log unknown sender

3. **Analyze Message Content:**
   - Pass SMS body to **Pulse Agent**
   - Determine if message indicates:
     - Medication adherence confirmation (keywords: "yes", "took", "done")
     - Symptom report (keywords from critical/warning symptom lists)
     - Request for help (keywords: "help", "question", "call me")

4. **Update Firestore:**
   - Log interaction in `/patients/{id}/interactions` with type `INBOUND_SMS`
   - If medication confirmed, create entry in `/medicationLog` with status `taken`
   - If symptoms reported, perform medical risk classification
   - Update `riskLevel` and `alert` fields if necessary

5. **Generate Response SMS:**
   - Acknowledge receipt: "Thank you for confirming, [Name]."
   - If critical symptoms detected: "We've alerted your nurse. They will call you shortly. If urgent, call 911."

#### **Response Specification**

**Success Response (200 OK):**

Twilio expects a **TwiML response** (XML) to optionally send a reply SMS.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Thank you for confirming, Sarah. Keep up the great recovery!</Message>
</Response>
```

**For Critical Symptoms Detected:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Thank you, Sarah. I've notified your nurse about your symptoms. They will call you within 15 minutes. If your condition worsens, please call 911.</Message>
</Response>
```

**Error Response (500):**

Log error internally but always return 200 to Twilio to prevent retries.

#### **Webhook Validation**

**Security Requirement:** Implement Twilio signature validation using the `twilio.request_validator` library or equivalent logic:

1. Construct validation string from URL and POST parameters
2. Compute HMAC-SHA1 hash using Twilio Auth Token
3. Compare with `X-Twilio-Signature` header (Base64 encoded)
4. Reject if mismatch

---

### **5.4. `POST /api/careflow/voice-alert`**

**Purpose:** Webhook endpoint for the **Caller Agent** to POST voice call results, including full conversation transcripts and telemetry.

#### **Request Specification**

**HTTP Method:** `POST`

**Headers:**

- `Content-Type: application/json`
- `X-A2A-Signature: {signature}` (for A2A protocol validation)

**Request Body Schema:**

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `callSid` | `string` | ✅ | Twilio call identifier | `"CA1234567890abcdef"` |
| `patientPhone` | `string` | ✅ | Patient's phone number | `"+15551234567"` |
| `callStatus` | `string` | ✅ | Final call status | `"completed"`, `"no-answer"`, `"busy"`, `"failed"` |
| `callDuration` | `number` | ❌ | Call duration in seconds | `180` (null if not completed) |
| `transcript` | `string` | ❌ | Full conversation transcript | `"Agent: Hello Sarah... Patient: I have chest pain..."` |
| `clinicalRisk` | `string` | ✅ | Suggested risk level from session | `"RED"` or `"GREEN"` |
| `timestamp` | `string` | ✅ | ISO 8601 timestamp | `"2025-11-15T08:20:45.123Z"` |

**Example Request (Completed Call):**

```json
{
  "callSid": "CA1234567890abcdef",
  "patientPhone": "+15551234567",
  "callStatus": "completed",
  "callDuration": 180,
  "transcript": "Agent: Good morning Sarah, this is CareFlow checking in on your recovery. How are you feeling today?\nPatient: Not good. I have chest pain and I'm dizzy.\nAgent: Thank you for telling me that, Sarah. For your safety, I'm alerting your nurse coordinator now.",
  "clinicalRisk": "RED",
  "timestamp": "2025-11-15T08:20:45.123Z"
}
```

**Example Request (No Answer):**

```json
{
  "callSid": "CA9876543210fedcba",
  "patientPhone": "+15552223333",
  "callStatus": "no-answer",
  "callDuration": null,
  "transcript": null,
  "clinicalRisk": "UNKNOWN",
  "timestamp": "2025-11-15T08:16:30.456Z"
}
```

#### **Processing Logic**

1. **Identify Patient:**
   - Query Firestore `/patients` where `contact.phone == {patientPhone}`
   - If not found, log error and return 200

2. **Handle Call Status:**

   **If `callStatus == "completed"` and transcript exists:**
    - Log interaction in `/patients/{id}/interactions` with type `OUTBOUND_CALL`
    - Include full transcript and call duration
    - Perform final medical risk classification
    - Update Firestore patient document with analysis results
    - Generate clinical summary (AI Brief)
    - If RED, alert assigned nurse

   **If `callStatus == "no-answer"` or `"busy"`:**
   - Log interaction with type `SYSTEM_EVENT` and status `no-answer`
   - Schedule retry call in 2 hours (add to Cloud Scheduler or in-memory queue)
   - Send SMS fallback: "Hi [Name], we tried to call but couldn't reach you. Please reply YES when you've taken your medication."

   **If `callStatus == "failed"`:**
   - Log error in interaction with reason
   - Create ORANGE alert for nurse to manually follow up
   - Do not retry (likely invalid number or service issue)

3. **Medication Adherence Tracking:**
   - If transcript contains confirmation of medication taken, create entry in `/medicationLog`
   - Parse medication names mentioned in transcript
   - Set status to `taken` with timestamp

#### **Response Specification**

**Success Response (200 OK):**

```json
{
  "status": "received",
  "patientId": "550e8400-e29b-41d4-a716-446655440000",
  "actionTaken": "Analyzed transcript, updated risk level to RED, nurse alerted",
  "timestamp": "2025-11-15T08:21:00.000Z"
}
```

**Error Response (200 OK with error details):**

Even on errors, return 200 to prevent webhook retries:

```json
{
  "status": "error",
  "message": "Patient not found for phone number",
  "timestamp": "2025-11-15T08:21:00.000Z"
}
```

---

### **5.5. Authentication & Authorization**

#### **Cloud Scheduler Authentication**

Google Cloud Scheduler authenticates to Agent Engine endpoints using:

**Method:** Service Account with IAM role `roles/run.invoker`

**Configuration:**

- Create service account: `scheduler-careflow@{project-id}.iam.gserviceaccount.com`
- Grant `Cloud Run Invoker` role on Agent Engine service
- Configure Cloud Scheduler jobs to use this service account's identity token

**Header Sent by Scheduler:**

```
Authorization: Bearer {GOOGLE_OIDC_TOKEN}
```

#### **Twilio Webhook Security**

**Method:** Signature validation using Twilio Auth Token

**Implementation Required:**

- Extract `X-Twilio-Signature` from request header
- Compute expected signature using Twilio library or manual HMAC-SHA1
- Compare signatures; reject if mismatch (return 403 Forbidden)

**Do NOT rely on IP allowlisting** (Twilio IPs can change)

#### **Caller Agent Webhook Security**

**Method:** A2A Protocol Authentication (JSON-RPC over SSE)

**Configuration:**

- Validate `X-A2A-Signature` using shared secret
- Reject requests with invalid message IDs or timestamps

---

### **5.6. Rate Limiting & Security**

#### **Rate Limiting Strategy**

**Cloud Scheduler Endpoints:**

- No explicit rate limiting needed (controlled by scheduler frequency)
- Expected traffic: 3 requests/day (morning, noon, evening)

**Webhook Endpoints (Twilio, A2A):**

- Implement per-endpoint rate limiting: **100 requests/minute**
- Per-source IP rate limiting: **10 requests/second**
- Rationale: Normal traffic is ~1 request per patient call; rate limits prevent abuse

**Implementation:**

- Use Google Cloud Armor (Layer 7 DDoS protection) in front of Agent Engine
- Configure rate limiting rules in Cloud Armor policy

#### **Security Headers**

All responses must include:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

#### **Request Size Limits**

- Maximum request body size: **1 MB** (sufficient for transcripts)
- Reject requests exceeding limit with `413 Payload Too Large`

#### **Logging & Monitoring**

**All endpoints must log:**

- Request timestamp and source IP
- Endpoint called and HTTP method
- Response status code and processing time
- Any errors encountered
- Patient ID (if identified) for audit trail

**Logs sent to:** Google Cloud Logging with structured format (JSON)

**Monitoring Alerts:**

- Alert if endpoint returns 5xx errors more than 5 times in 5 minutes
- Alert if endpoint latency exceeds 5 seconds
- Alert if authentication failures spike (potential attack)

---

## **6. External Integrations**

CareFlow Pulse relies on a coordinated ecosystem of medical-grade and voice-optimized services to provide seamless patient monitoring.

### **6.1. Twilio ConversationRelay**

The **Caller Agent** uses Twilio ConversationRelay to bridge professional telephony with real-time AI processing.

- **Audio Streaming:** Bi-directional 8kHz μ-law audio stream via WebSockets.
- **Interruption Handling:** Native barge-in detection with sub-100ms response suspension.
- **Protocol:** TwiML `<Connect><ConversationRelay /></Connect>` with dynamic session parameters.
- **Webhook Integration:** Receives `session_ended` and `transcript` payloads.

### **6.2. ElevenLabs TTS**

For high-fidelity, empathetic medical personas, we integrate ElevenLabs via the `ElevenLabs SDK`.

- **Voice Configuration:** `21m00Tcm4TlvDq8ikWAM` (Rachel) - Selected for clarity and professional tone.
- **Latency Control:** PCM 44.1kHz delivery with frame-level chunking to maintain sub-500ms TTFB (Time To First Byte).
- **Stability/Clarity:** Optimized for medical terminology pronunciation.

### **6.3. Google Cloud Platform (GCP)**

- **Vertex AI:** Powers the Pulse Agent (Gemini 3 Flash) for clinical reasoning.
- **Model Armor:** Serves as the security firewall for PII/PHI redaction.
- **Cloud Run:** Hosts the stateless Agent Fleet with multi-tenant isolation.
- **Firebase/Firestore:** Provides the real-time document store for patient telemetry.

---

## **7. Frontend: Next.js Application**

The CareFlow Dashboard is a modern, real-time interface designed for nurse efficiency and rapid triage.

### **7.1. Technology Stack**

- **Framework:** Next.js 16.0.9 (App Router)
- **Real-time:** `firebase/firestore` snapshots for instant alert propagation.
- **Auth:** `NextAuth.js` with Hospital ID session grounding.
- **Styling:** Tailwind CSS with a clean, medical-grade design system.

### **7.2. Architecture Principles**

- **Optimistic Updates:** UI reflects actions immediately while syncing to Firestore in the background.
- **Role-Based Views:** Nurses see only their assigned patients and active hospital branch.
- **Component isolation:** Atomic design pattern for high reusability of charts, logs, and alert cards.

### **7.3. Real-Time Data Patterns**

The dashboard implements **real-time Firestore listeners** using the `onSnapshot` API, enabling instant propagation of alerts created by the AI agents.

#### **7.3.1. useAlerts Hook**

A custom React hook that subscribes to the `alerts` collection with live updates:

```typescript
// src/hooks/useAlerts.ts
export function useAlerts(hospitalId: string = "HOSP001") {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const alertsRef = collection(db, "alerts");
        const q = query(
            alertsRef,
            where("hospitalId", "==", hospitalId),
            orderBy("createdAt", "desc")
        );

        // Real-time subscription
        const unsubscribe = onSnapshot(q, (snapshot) => {
            const allAlerts = snapshot.docs.map(doc => ({
                id: doc.id,
                ...doc.data()
            }));
            // Client-side filter for active status
            const activeAlerts = allAlerts.filter(
                a => a.status === "active" || a.status === "in_progress"
            );
            setAlerts(activeAlerts);
            setLoading(false);
        });

        return () => unsubscribe();
    }, [hospitalId]);

    const criticalCount = alerts.filter(
        a => a.priority === "critical" || a.priority === "warning"
    ).length;

    return { alerts, loading, criticalCount };
}
```

**Key Features:**

- Auto-cleanup on unmount
- Hospital-scoped queries (multi-tenant)
- Client-side status filtering (avoids composite index)
- Returns `criticalCount` for sidebar badge

#### **7.3.2. Real-Time Components**

| Component | File | Purpose |
| :--- | :--- | :--- |
| `AlertsRealtime` | `src/components/alerts/AlertsRealtime.tsx` | Renders live-updating alert list with loading skeleton |
| `AppSidebar` | `src/components/layout/AppSidebar.tsx` | Displays real-time badge with critical alert count |

**Alert Flow:**

```
Agent creates alert → Firestore write → onSnapshot fires → UI updates instantly
```

### **7.4. Key Components & Pages**

#### **Dashboard Layout** (`app/(dashboard)/layout.tsx`)

The main layout wraps all authenticated pages with:

- `SidebarProvider` for collapsible navigation
- `AppSidebar` with real-time alert badge
- Header with sign-out button

#### **Pages Overview**

| Route | Component | Data Source |
| :--- | :--- | :--- |
| `/dashboard` | KPI cards, risk chart | Server-side via `getDashboardStats()` |
| `/alerts` | `AlertsRealtime` | **Real-time** via `useAlerts()` |
| `/patients` | Patient list | Server-side via `getPatients()` |
| `/patient/[id]` | Patient profile (3-column) | Server-side via `getPatient()` |
| `/config` | System settings | Server-side |

#### **Database Layer** (`src/lib/db.ts`)

Server-side utility functions for Next.js Server Components:

| Function | Returns |
| :--- | :--- |
| `getPatients()` | All patients for current hospital |
| `getPatient(id)` | Single patient with full details |
| `getAlerts()` | Active alerts (used for initial page load) |
| `getDashboardStats()` | Aggregated KPIs and status counts |

---

## **8. Data Flow & User Journeys**

### **8.1. Journey: Automated Morning Rounds**

1. **Trigger:** Cloud Scheduler POSTs to `/api/careflow/trigger-scheduled-calls` at 08:15 AM.
2. **Orchestration:** Pulse Agent queries patients with `scheduleHour: 8`.
3. **Delegation:** Pulse Agent sends A2A tasks to Caller Agent for each patient.
4. **Interaction:** Caller Agent conducts the call via Twilio + ElevenLabs.
5. **Collection:** After hangup, Caller Agent POSTs full transcript and telemetry to Pulse Agent.
6. **Closing:** Pulse Agent updates Firestore and, if necessary, triggers an Alert.

### **8.2. Journey: Critical Symptom Triage**

1. **Detection:** During a call, the patient mentions "Chest pain."
2. **Escalation:** Caller Agent pauses the interview and initiates stable handover.
3. **Alerting:** Pulse Agent creates a **RED** alert in `/alerts` with an AI Brief.
4. **Visibility:** The Nurse Dashboard flashes Red and plays an audible tone.
5. **Intervention:** The Nurse Coordinator clicks "Take Ownership" and initiates manual contact.

---

## **9. Security & Compliance**

CareFlow Pulse implements a multi-layered security strategy designed for healthcare environments, focusing on data privacy, multi-tenant isolation, and AI safety.

### **9.1. Data Encryption & Integrity**

- **At-Rest:** All data in Google Cloud Firestore is encrypted using Google-managed encryption keys.
- **In-Transit:** TLS 1.2+ is enforced for all API traffic (Frontend to Backend, Agent-to-Agent).
- **Integrity:** Point-in-Time Recovery (PITR) enabled in Firestore for 7-day data resilience.

### **9.2. Multi-Tenant Isolation**

- **Logical Separation:** Every patient, interaction, and alert document is tagged with a `hospitalId`.
- **Database Rules:** Firestore security rules enforce Row-Level Security (RLS), preventing users or agents from accessing data outside their assigned hospital.
- **Agent Scoping:** Each agent service is deployed with a strict `HOSPITAL_ID` environment variable that acts as a hard boundary for all tool-driven database queries.

### **9.3. AI Safety & Model Armor**

The system incorporates **Google Cloud Model Armor** as a dedicated security firewall between users and the AI models (Gemini).

- **Fail-Closed Policy:** In accordance with clinical safety standards, the security layer defaults to "Blocked" if the Model Armor service becomes unreachable or returns an error.
- **Prompt Injection Defense:** Scans all incoming user messages (voice transcripts and SMS) for adversarial patterns, jailbreak attempts, or instructions designed to override the medical clinical persona.
- **Output Sanitization (PHI Redaction):** All model responses are scanned for Protected Health Information (PHI) and redacted in real-time before being sent to the Caller Agent or displayed on the dashboard.
- **SDK & Infrastructure:** Uses `google-cloud-modelarmor >= 0.3.0` with localized regional endpoints (`modelarmor.us.rep.googleapis.com`) for minimal latency and high policy discovery reliability.

### **9.4. HIPAA Compliance Considerations**

- **BAA Scope:** Built exclusively on Google Cloud services covered by the Business Associate Agreement (BAA).
- **Minimal Access:** AI agents only access the specific patient fields required for the current clinical context.
- **Identity:** NextAuth.js provides secure JWT-based authentication for all staff members.

### **9.5. Audit Logging**

- **System Actions:** All patient data modifications are logged to the `audit_logs` collection.
- **Security Events:** Unauthorized access attempts and Model Armor block events are recorded in Google Cloud Logging for security review.
- **Immutability:** Audit logs are protected by Firestore rules to prevent modification or deletion.

### **9.6. Reference Documentation**

For more detailed information, refer to:

- [HIPAA Compliance Technical Guide](file:///home/audrey/Bureau/careflow/docs/hipaa_compliance_guide.md)
- [Frontend Security Checklist](file:///home/audrey/Bureau/careflow/docs/FRONTEND-SECURITY.md)
- [Security Audit Report](file:///home/audrey/Bureau/careflow/docs/security_audit_report.md)

---

## **10. Configuration & Environment Variables**

### **10.1. Backend Environment Variables (The Fleet)**

Each Agent Service in the fleet requires specific configuration.

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `HOSPITAL_ID` | ✅ | **[CRITICAL]** Tenant Context for this Agent Instance | `"HOSP001"` |
| `FIREBASE_PROJECT_ID` | ✅ | Firebase Project ID | `"careflow-478811"` |
| `GOOGLE_CLOUD_PROJECT` | ✅ | GCP Project ID | `"careflow-478811"` |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio Account SID | `"AC..."` |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio Auth Token | `"..."` |
| `ELEVENLABS_API_KEY` | ✅ | ElevenLabs API Key | `"..."` |
| `A2A_SECRET` | ✅ | Secret for Inter-Agent Auth | `"..."` |

---

## **11. Deployment Guide**

### **11.2. Infrastructure as Code (Terraform)**

Deployment of core infrastructure is managed via **Terraform** to ensure consistency across environments.

#### **Cloud Scheduler Configuration**

Automated patient rounds are triggered by Cloud Scheduler jobs.

```hcl
resource "google_cloud_scheduler_job" "morning_rounds" {
  name             = "morning-rounds-hosp001"
  description      = "Trigger morning patient rounds for HOSP001"
  schedule         = "0 8 * * *"
  time_zone        = "America/New_York"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.pulse_agent.status[0].url}/api/careflow/trigger-scheduled-calls"
    body        = base64encode("{\"timeSlot\": \"morning\", \"hour\": 8}")
    
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}
```

#### **IAM Roles & Service Accounts**

Strict IAM bindings enforce the principle of least privilege.

| Service Account | Role | Purpose |
| :--- | :--- | :--- |
| `pulse-agent-sa` | `roles/datastore.user` | Firestore CRUD access |
| `pulse-agent-sa` | `roles/aiplatform.user` | Vertex AI / Gemini access |
| `scheduler-sa` | `roles/run.invoker` | Permission to trigger Agent endpoints |
| `pulse-agent-sa` | `roles/modelarmor.user` | Access to Model Armor security policies |

#### **GCP Project Scoping**

Terraform modules are scoped by `HOSPITAL_ID` to support factory-style replication for new tenants.

---

#### **Agent 2: CareFlow Caller Agent (Voice Interface)**

**Purpose:** Handles voice interactions via Twilio ConversationRelay, streams audio with ElevenLabs, receives A2A messages from Pulse Agent.

**Deployment**:

```bash
cd careflow-agents/caller-agent

# Build and deploy to Cloud Run
make deploy

# Or manually:
gcloud builds submit --tag gcr.io/careflow-478811/caller-agent:latest
gcloud run deploy caller-agent \
  --image gcr.io/careflow-478811/caller-agent:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars TWILIO_ACCOUNT_SID=ACxxx,TWILIO_AUTH_TOKEN=xxx,ELEVENLABS_API_KEY=xxx
```

**Environment Variables**:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel voice
GOOGLE_CLOUD_PROJECT=careflow-478811
```

**Exposed Endpoints**:

- `POST /` - A2A protocol endpoint (receives messages from Pulse Agent)
- `POST /twilio-webhook` - Twilio voice status callbacks

---

### **11.2. Cloud Scheduler Deployment (Terraform)**

The **Cloud Scheduler** orchestrates automated daily patient rounds by triggering the CareFlow Pulse Agent at predetermined times.

#### **Architecture**

```
Cloud Scheduler (Morning/Noon/Evening)
    ↓ HTTPS POST with OIDC Auth
CareFlow Pulse Agent
    ↓ A2A Protocol
CareFlow Caller Agent
    ↓ Twilio API
Patient Phone Calls
```

#### **Infrastructure as Code**

All scheduler resources are managed via **Terraform** in `scheduler/terraform/`:

**File Structure**:

```
scheduler/terraform/
├── main.tf          # Scheduler jobs (3 times × 2 environments = 6 jobs)
├── variables.tf     # prod_project_id, staging_project_id, pulse_agent_urls
├── outputs.tf       # Service account emails, job names
├── providers.tf     # Google Cloud provider with staging/prod aliases
└── vars/
    └── env.tfvars   # Configuration values
```

#### **Multi-Environment Strategy**

Uses `for_each` loops to deploy to **staging and production simultaneously**:

```terraform
locals {
  deploy_project_ids = {
    prod    = var.prod_project_id
    staging = var.staging_project_id
  }
}

resource "google_cloud_scheduler_job" "morning_rounds" {
  for_each = local.deploy_project_ids  # Creates 2 jobs

  name    = "${var.project_name}-morning-rounds"
  project = each.value
  schedule = "15 8 * * *"  # 8:15 AM EST
  time_zone = "America/New_York"
  
  http_target {
    http_method = "POST"
    uri = var.pulse_agent_urls[each.key]
    
    body = base64encode(jsonencode({
      scheduleHour = 8
      timezone     = "America/New_York"
      triggerType  = "scheduled"
      source       = "cloud-scheduler"
      environment  = each.key
    }))
    
    oidc_token {
      service_account_email = google_service_account.scheduler_sa[each.key].email
      audience = var.pulse_agent_urls[each.key]
    }
  }
}
```

#### **Schedule Configuration**

| Job | Time (EST) | Cron | Purpose |
|-----|------------|------|---------|
| `careflow-morning-rounds` | 8:15 AM | `15 8 * * *` | Post-breakfast medication adherence |
| `careflow-noon-rounds` | 12:15 PM | `15 12 * * *` | Mid-day symptom check |
| `careflow-evening-rounds` | 8:15 PM | `15 20 * * *` | Evening medication review |

**Total Resources Deployed**: 16

- 6 Cloud Scheduler Jobs (3 × staging + 3 × prod)
- 2 Service Accounts (`careflow-scheduler`)
- 2 IAM Bindings (`roles/run.invoker`)
- 6 API Enablements (`cloudscheduler.googleapis.com`, etc.)

#### **Deployment Steps**

**Step 1: Configure Variables**

```bash
cd scheduler/terraform
nano vars/env.tfvars
```

```terraform
# Project IDs
prod_project_id    = "careflow-478811"
staging_project_id = "careflow-staging-12345"
project_name       = "careflow"

# Region
region = "us-central1"

# Pulse Agent URLs (from Cloud Run deployment)
pulse_agent_urls = {
  prod    = "https://careflow-agent-abc123-uc.a.run.app"
  staging = "https://careflow-agent-xyz789-uc.a.run.app"
}

pulse_agent_service_name = "careflow-agent"
```

**Step 2: Initialize Terraform**

```bash
terraform init
```

**Step 3: Preview & Deploy**

```bash
terraform plan -var-file=vars/env.tfvars
terraform apply -var-file=vars/env.tfvars
```

**Step 4: Verify Deployment**

```bash
# List scheduler jobs
gcloud scheduler jobs list --project=careflow-478811 --location=us-central1

# Manually trigger test
gcloud scheduler jobs run careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1
```

#### **Security: OIDC Authentication**

Cloud Scheduler authenticates to Cloud Run using **OIDC tokens** (no API keys):

1. **Service Account**: `careflow-scheduler@{project}.iam.gserviceaccount.com`
2. **IAM Role**: `roles/run.invoker` on CareFlow Pulse Agent
3. **Token Generation**: Automatically signed by scheduler SA
4. **Validation**: Cloud Run verifies audience and issuer

**IAM Binding** (managed by Terraform):

```terraform
resource "google_cloud_run_v2_service_iam_member" "pulse_agent_invoker" {
  for_each = local.deploy_project_ids

  project  = each.value
  location = var.region
  name     = var.pulse_agent_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa[each.key].email}"
}
```

#### **Retry Configuration**

Each job has automatic retry logic:

```terraform
retry_config {
  retry_count          = 3       # Max 3 attempts
  max_retry_duration   = "0s"
  min_backoff_duration = "60s"   # 1 minute wait
  max_backoff_duration = "300s"  # 5 minutes max
}
```

**Retry Scenarios**:

- Cloud Run cold start delays
- Temporary network failures
- Downstream service rate limiting

#### **Operations**

**Pause Jobs** (Maintenance):

```bash
for job in morning-rounds noon-rounds evening-rounds; do
  gcloud scheduler jobs pause careflow-$job \
    --project=careflow-478811 --location=us-central1
done
```

**Resume Jobs**:

```bash
for job in morning-rounds noon-rounds evening-rounds; do
  gcloud scheduler jobs resume careflow-$job \
    --project=careflow-478811 --location=us-central1
done
```

**Update Schedule**:
Edit `main.tf`, change `schedule` parameter, then:

```bash
terraform apply -var-file=vars/env.tfvars
```

#### **Monitoring**

**Key Metrics**:

1. Job success rate: `cloudscheduler.googleapis.com/job/attempt_count`
2. Execution duration: `cloudscheduler.googleapis.com/job/execution_duration`
3. Agent response latency: `run.googleapis.com/request_latencies`

**Alert Policy** (3 consecutive failures):

```bash
gcloud alpha monitoring policies create \
  --display-name="CareFlow Scheduler Failures" \
  --condition-threshold-value=3 \
  --condition-filter='resource.type="cloud_scheduler_job"'
```

**Cost**: ~$4/year for 6 jobs (3 free, 3 × $0.10/month)

For complete documentation, see: [`scheduler/README.md`](../scheduler/README.md)

---

### **11.3. Frontend Deployment (Vercel)**

The Next.js frontend is deployed as a single application.

- **Environment:**
  - `NEXT_PUBLIC_FIREBASE_PROJECT_ID=careflow-478811`
- **Multi-Tenancy:**
  - The frontend uses the logged-in user's `hospitalId` (from Auth session) to filter data views.
  - No separate deployment is needed for the frontend.

---

## **12. Testing Strategy & Benchmarks**

CareFlow Pulse follows a multi-layered testing strategy to ensure clinical safety and technical reliability. Crucially, our benchmarks directly inform architectural decisions, ensuring that trade-offs between latency, security, and intelligence are data-driven.

---

### **12.1. Benchmark-Driven Architecture**

#### **12.1.1. Model Latency Benchmark**

**Goal:** Evaluate Gemini model variants for real-time voice suitability.

| Model | Avg TTFT (ms) | Stability | Suitability for Voice |
| :--- | :--- | :--- | :--- |
| **gemini-2.0-flash** | **~527 ms** | High | 🟢 **Ideal** |
| gemini-2.5-flash | ~1,228 ms | Moderate | 🟡 Acceptable (barely) |
| gemini-3.0-flash | ~1,550 ms | Moderate | 🔴 Too Slow for Real-time |
| gemini-3.0-pro | ~4,200 ms | Low | ❌ Reasoning Only |

*TTFT = Time To First Token.*

**Architectural Decision → Hybrid Model Strategy:**

1. **Caller Agent (Voice):** `gemini-2.0-flash` for speed (~527ms TTFT).
   - *Reasoning:* Voice requires sub-800ms response to avoid "dead air."
   - *Mitigation:* Complex decisions are delegated to the Pulse Agent.

2. **Pulse Agent (Medical Brain):** `gemini-3-pro-preview` for intelligence.
   - *Reasoning:* Asynchronous processing; latency irrelevant, correctness critical.

**Run Benchmark:**

```bash
cd careflow-agents/caller-agent
python benchmarking/latency_benchmark.py
```

---

#### **12.1.2. Security Latency Benchmark (Model Armor)**

**Goal:** Measure latency overhead of Google Cloud Model Armor for different security tiers.

| Tier | Description | Protection | Latency Overhead |
| :--- | :--- | :--- | :--- |
| **Tier 1** | Prompt Scanning Only | Jailbreak/Injection Prevention | **~264 ms** |
| **Tier 2** | Full Bidirectional | Tier 1 + PII/PHI Redaction | **~510 ms** (Cumulative) |

**Architectural Decision → Tiered Security Model:**

1. **Caller Agent (Voice) → TIER 1 ONLY**
   - *Context:* Real-time voice requires <800ms total latency.
   - *Implementation:* ENABLE `scan_prompt`, DISABLE `sanitize_response`.
   - *Reasoning:* Trusts Gemini 2.0 Flash output; redaction adds ~250ms degrading voice UX.

2. **Pulse Agent (Background) → TIER 2 (FULL)**
   - *Context:* Asynchronous analysis of patient data.
   - *Implementation:* ENABLE both `scan_prompt` and `sanitize_response`.
   - *Reasoning:* Latency not critical; maximum PHI protection required.

**Run Benchmark:**

```bash
cd careflow-agents/careflow-agent
python benchmarks/security/benchmark_tiered_security.py
```

---

### **12.2. Protocol Verification ("Teach-Back" Evaluation)**

**Goal:** Ensure the agent correctly identifies when a patient understands or misunderstands clinical instructions.

#### **Evaluation Tiers:**

| Tier | Method | Use Case |
| :--- | :--- | :--- |
| **Tier 1** | Regex-Based (Fast) | CI/CD quick checks |
| **Tier 2** | LLM-as-a-Judge (Gemini 3 Pro) | Deep clinical safety verification |

#### **LLM-as-a-Judge Results:**

| Scenario | Protocol | Patient Response | Expected | Agent | Judge |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **001** | Weight Monitoring | "Call if +10lbs/month" | **FAIL** | **FAIL** | ✅ |
| **002** | Medication (Lasix) | "Morning with breakfast" | **PASS** | **PASS** | ✅ |
| **003** | Red Flag Symptoms | "Tired or headache" | **FAIL** | **FAIL** | ✅ |
| **004** | Sodium Diet | "Eat salad, avoid junk" | **FAIL** | **FAIL** | ✅ |

**Total Accuracy: 100%**

**Example Scenario (Heart Failure Red Flag):**

- **Nurse:** "When should you call the doctor regarding your weight?"
- **Patient:** "I think you said I should call if I gain 10 pounds in a month."
- **Correct Answer:** "I should call if I gain 3 pounds in a day or 5 pounds in a week."
- **Expected:** FAIL (Protocol is 3 lbs overnight or 5 lbs/week; 10 lbs/month is too late)

**Run Evaluation:**

```bash
cd careflow-agents/careflow-agent
python tests/protocol_evals/llm_as_judge/test_teach_back_judge.py
```

---

### **12.3. Audio Handoff Testing (v3.4)**

**Goal:** Verify the Audio-First Reporting flow between Caller Agent and Pulse Agent.

**Test Flow:**

1. Simulates a "Call Finished" message from Caller Agent with `callSid`.
2. Verifies that Pulse Agent calls `fetch_call_audio` tool.
3. Mocks Twilio Recordings API and Gemini multimodal analysis.
4. Asserts that clinical report is generated from audio content.

**Run Test:**

```bash
cd careflow-agents/careflow-agent
python tests/audio_handoff/test_audio_flow.py
```

---

### **12.4. Load Testing (Locust)**

**Goal:** Stress test the agent under concurrent request loads.

**Configuration:**

- Framework: Locust
- Duration: 30 seconds
- Users: Up to 60 concurrent (spawn rate: 2/sec)

**Local Testing:**

```bash
# Terminal 1: Start Server
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000

# Terminal 2: Run Load Test
python3 -m venv .locust_env && source .locust_env/bin/activate && pip install locust==2.31.1 a2a-sdk~=0.3.9

locust -f tests/load_test/load_test.py \
  -H http://127.0.0.1:8000 \
  --headless -t 30s -u 60 -r 2 \
  --csv=tests/load_test/.results/results \
  --html=tests/load_test/.results/report.html
```

**Remote Testing (Cloud Run):**

```bash
export RUN_SERVICE_URL=https://your-cloud-run-service-url.run.app
export _ID_TOKEN=$(gcloud auth print-identity-token -q)

locust -f tests/load_test/load_test.py \
  -H $RUN_SERVICE_URL \
  --headless -t 30s -u 60 -r 2 \
  --csv=tests/load_test/.results/results \
  --html=tests/load_test/.results/report.html
```

---

### **12.5. Unit & Integration Testing**

| Layer | Framework | Coverage |
| :--- | :--- | :--- |
| **Backend (Python)** | `pytest` | Tool logic, Firestore interactions, Model Armor plugin |
| **Frontend (Next.js)** | `Vitest`, `React Testing Library` | Dashboard components, form validation |
| **API E2E** | `Playwright` | Full round-triggering flow |

**Run Backend Tests:**

```bash
cd careflow-agents/careflow-agent
uv run pytest tests/
```

---

### **12.6. Manual Voice Testing**

Given the voice nature of the Caller Agent, manual "Golden Path" call sessions are conducted weekly to verify:

- ElevenLabs voice latency and emotional resonance.
- Twilio ConversationRelay barge-in sensitivity.
- Patient distress detection accuracy (Audio-First v3.4).

---

## 13. Performance Optimization

### 13.1. Voice Latency Hierarchy

To achieve natural conversation flow, we target sub-2s response latency:

1. **Streaming STT (Twilio):** Real-time transcriptions sent to Caller Agent.
2. **Streaming LLM (Gemini):** Partial chunks sent to TTS as soon as context is sufficient.
3. **Streaming TTS (ElevenLabs)::** Audio frames streamed back to Twilio immediately.

### 13.2. Database Performance

- **Firestore Indexing:** Composite indexes on `hospitalId` + `riskLevel` + `createdAt` for sub-100ms dashboard refreshes.
- **Caching:** Pulse Agent caches hospital-specific configuration for 30 minutes to reduce Firestore reads.

---

## 14. Error Handling & Monitoring

### 14.1. Clinical Safety Handover

If the AI Agent detects an unrecoverable error or high patient distress:

1. **Fallback Message:** "I'm having trouble connecting to my medical systems. Please stay on the line, I'm alerting your nurse coordinator immediately."
2. **Escalation:** Triggers a `roles/critical_handover` alert in Firestore.

### 14.2. Operational Monitoring

- **Google Cloud Logging:** All agent thoughts and tool calls are logged with `TRACE` level.
- **Error Reporting:** Real-time alerts on HTTP 5xx or Model Armor block spikes.
- **Custom Telemetry:** Tracks "Time to Handover" and "Call Completion Rate" per hospital.

---

## 15. Future Enhancements & Roadmap

### 15.1. Vision-Based Adherence (v3.5)

Allow patients to text photos of their medication bottles to the Pulse Agent for automatic verification using Gemini Multimodal Vision.

### 15.2. EHR Integration (v4.0)

Direct HL7 FHIR integration with Epic and Cerner to eliminate manual patient data entry.

---

## **Appendices**

- **Appendix A:** [ADK Prompt Engineering Guide](file:///home/audrey/Bureau/careflow/docs/prompt_engineering.md)

- **Appendix B:** [Infrastructure Blueprint (Terraform Resources)](file:///home/audrey/Bureau/careflow/docs/infrastructure_blueprint.md)
