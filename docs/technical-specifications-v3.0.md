# **CareFlow Pulse: Technical Specifications (v2.0)**

| | |
| :--- | :--- |
| **Document Version:** | 3.0 |
| **Date:** | 2025-12-03 |
| **Status:** | **Current** |
| **Author:** | Christ |

---

## **Revision History**
| Version | Date | Author | Changes |
| :--- | :--- | :--- | :--- |
| 1.0 | 2025-11-15 | Christ | Initial Draft - Basic architecture overview |
| 2.0 | 2025-11-15 | Christ | Complete rewrite with comprehensive database structure, API endpoints, and implementation details |
| 3.0 | 2025-12-03 | Christ | Major architecture update: Dual-agent system (CareFlow Pulse + Caller), MCP protocol integration, A2A inter-agent communication, Twilio ConversationRelay, Cloud Run deployment |

---

## **Table of Contents**

### **1. Introduction**
   - 1.1. Purpose of this Document
   - 1.2. Intended Audience
   - 1.3. Document Scope
   - 1.4. References & Dependencies

### **2. System Architecture Overview**
   - 2.1. High-Level Architecture Diagram
   - 2.2. Technology Stack
   - 2.3. Component Interaction Flow
   - 2.4. Deployment Architecture

### **3. Database Design (Firestore)**
   - 3.1. Overview & Design Principles
   - 3.2. Collection: `/patients`
   - 3.3. Sub-Collection: `/patients/{patientId}/interactions`
   - 3.4. Sub-Collection: `/patients/{patientId}/medicationLog`
   - 3.5. Collection: `/alerts`
   - 3.6. Collection: `/users`
   - 3.7. Indexes & Query Optimization
   - 3.8. Security Rules
   - 3.9. Data Migration & Seeding

### **4. Backend: Dual-Agent AI System**
   - 4.1. Architecture Overview: Two Specialized Agents
   - 4.2. CareFlow Pulse Agent (Medical Intelligence)
      - 4.2.1. Google ADK Implementation
      - 4.2.2. MCP Protocol Integration
      - 4.2.3. Firestore Tools (6 MCP Tools)
      - 4.2.4. A2A Server Configuration
   - 4.3. CareFlow Caller Agent (Voice Interface)
      - 4.3.1. LangGraph REACT Architecture
      - 4.3.2. Twilio ConversationRelay Integration
      - 4.3.3. ElevenLabs TTS Configuration
      - 4.3.4. A2A Client for Medical Agent Delegation
   - 4.4. MCP (Model Context Protocol)
      - 4.4.1. Toolbox Executable Setup
      - 4.4.2. Firestore Connection Configuration
      - 4.4.3. Available MCP Tools
   - 4.5. A2A (Agent-to-Agent Protocol)
      - 4.5.1. Protocol Overview (JSON-RPC + SSE)
      - 4.5.2. AgentCard Definition
      - 4.5.3. Inter-Agent Communication Flow
   - 4.6. Prompt Engineering Strategy
   - 4.7. Error Handling & Fallback Logic

### **5. Backend: API Endpoints**
   - 5.1. Endpoint Overview
   - 5.2. `POST /api/careflow/trigger-scheduled-calls`
   - 5.3. `POST /api/careflow/twilio-sms`
   - 5.4. `POST /api/careflow/voice-alert`
   - 5.5. Authentication & Authorization
   - 5.6. Rate Limiting & Security

### **6. External Integrations**
   - 6.1. Twilio ConversationRelay (Voice AI)
      - 6.1.1. WebSocket Connection Setup
      - 6.1.2. Real-Time Voice Streaming
      - 6.1.3. Webhook Configuration
      - 6.1.4. TwiML Endpoint Implementation
   - 6.2. ElevenLabs (Text-to-Speech)
      - 6.2.1. Voice Selection & Configuration
      - 6.2.2. Integration with ConversationRelay
      - 6.2.3. Latency Optimization
   - 6.3. Twilio SMS
      - 6.3.1. SMS Messaging Flow
      - 6.3.2. Patient Response Handling
   - 6.4. Google Cloud Run
      - 6.4.1. Deployment Configuration (2 Services)
      - 6.4.2. Environment Variables Setup
      - 6.4.3. Service Communication
      - 6.4.4. Scaling & Performance

### **7. Frontend: Next.js Application**
   - 7.1. Application Structure
   - 7.2. Authentication System (NextAuth)
      - 7.2.1. User Roles & Permissions
      - 7.2.2. Session Management
      - 7.2.3. Protected Routes
   - 7.3. Dashboard Pages
      - 7.3.1. `/dashboard` - Overview
      - 7.3.2. `/patients` - Patient List
      - 7.3.3. `/patient/{patientId}` - Patient Detail
      - 7.3.4. `/alerts` - Alert Management
      - 7.3.5. `/config` - System Configuration
   - 7.4. Real-Time Data Synchronization
   - 7.5. State Management Strategy
   - 7.6. UI Component Library (shadcn/ui)

### **8. Data Flow & User Journeys**
   - 8.1. Scheduled Patient Follow-Up (Green Path)
   - 8.2. Critical Alert Generation (Red Path)
   - 8.3. Nurse Alert Response Workflow
   - 8.4. Patient SMS Reply Flow
   - 8.5. Medication Adherence Tracking

### **9. Security & Compliance**
   - 9.1. Data Encryption
   - 9.2. Authentication & Authorization
   - 9.3. HIPAA Compliance Considerations
   - 9.4. Audit Logging
   - 9.5. Data Retention & Deletion Policies

### **10. Configuration & Environment Variables**
   - 10.1. Backend Environment Variables
   - 10.2. Frontend Environment Variables
   - 10.3. Twilio Configuration
   - 10.4. Google Cloud Configuration

### **11. Deployment Guide**
   - 11.1. Backend Deployment (Google Cloud Run - 2 Services)
   - 11.2. Frontend Deployment (Vercel)
   - 11.3. Database Setup (Firestore)
   - 11.4. MCP Toolbox Setup
   - 11.5. CI/CD Pipeline
   - 11.6. Monitoring & Logging

### **12. Testing Strategy**
   - 12.1. Unit Testing
   - 12.2. Integration Testing
   - 12.3. End-to-End Testing
   - 12.4. Load Testing
   - 12.5. Test Data & Mocking

### **13. Performance Optimization**
   - 13.1. Database Query Optimization
   - 13.2. Frontend Performance
   - 13.3. API Response Times
   - 13.4. Caching Strategy

### **14. Error Handling & Monitoring**
   - 14.1. Error Classification
   - 14.2. Logging Strategy
   - 14.3. Alerting & Notifications
   - 14.4. Debugging Tools

### **15. Future Enhancements & Roadmap**
   - 15.1. EHR Integration
   - 15.2. Patient Mobile App
   - 15.3. Advanced Analytics Dashboard
   - 15.4. Multi-Language Support
   - 15.5. Predictive ML Models

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
- **Integration specifications** for third-party services (Twilio, Deepgram, Google Cloud)
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
   - Deepgram for AI-powered voice conversations
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

❌ **Multi-Language Support** - v1.0 is English-only; internationalization is planned for v1.3

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
- google-adk >= 1.6.1 (CareFlow Pulse Agent)
- langgraph (CareFlow Caller Agent)
- langchain-google-genai >= 2.0.7
- a2a-sdk (Agent-to-Agent communication)
- toolbox-core (MCP protocol)
- python-dotenv
- Deployed on Google Cloud Run (2 separate services)

**Frontend:**
- Node.js 18+ / npm or bun
- Next.js 16.0.3
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

#### **Conventions Used in This Document**

Throughout this technical specification, the following conventions are used:

- **`Code blocks`** represent actual code, configuration, or terminal commands
- **Field names** in database schemas are shown in `monospace font`
- **[Hyperlinks]** point to related sections, external documentation, or code repositories
- **⚠️ Warning boxes** highlight critical security or performance considerations
- **💡 Pro Tips** provide implementation best practices
- **🔧 TODO markers** indicate areas requiring additional configuration or future enhancement

---

## **2. System Architecture Overview**

### **2.1. High-Level Architecture Diagram**

CareFlow Pulse is built on a **modern dual-agent architecture** using cutting-edge protocols (MCP, A2A) for healthcare data access and inter-agent communication. The system separates concerns between medical intelligence, voice interaction, and user interfaces.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CAREFLOW PULSE ARCHITECTURE v3.0                    │
│                  Dual-Agent System with MCP & A2A Protocols                 │
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
    │                  GOOGLE CLOUD RUN (us-central1)              │
    │                                                               │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │   CareFlow Caller Agent (Port 8080)                 │   │
    │  │   LangGraph REACT Architecture                      │   │
    │  │                                                       │   │
    │  │  • Voice conversation management                    │   │
    │  │  • Twilio ConversationRelay integration             │   │
    │  │  • ElevenLabs TTS (voice: UgBBYS2sOqTuMpoF3BR0)    │   │
    │  │  • A2A Client for medical agent delegation          │   │
    │  │  • Conversation state tracking                      │   │
    │  └──────────────────┬──────────────────────────────────┘   │
    │                     │                                        │
    │                     │ A2A Protocol (JSON-RPC + SSE)         │
    │                     │ http://careflow-pulse-agent:8000      │
    │                     ▼                                        │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │   CareFlow Pulse Agent (Port 8000)                  │   │
    │  │   Google ADK Implementation                         │   │
    │  │                                                       │   │
    │  │  • Medical reasoning & triage                       │   │
    │  │  • MCP Toolbox integration (6 Firestore tools)      │   │
    │  │  • Clinical decision support                        │   │
    │  │  • Risk assessment (GREEN/ORANGE/RED)               │   │
    │  │  • A2A Server for caller agent requests             │   │
    │  │  • AgentCard: /.well-known/agent.json              │   │
    │  └──────────────────┬──────────────────────────────────┘   │
    └─────────────────────┼──────────────────────────────────────┘
                          │
                          │ MCP Protocol
                          │ http://localhost:5000
                          ▼
              ┌─────────────────────────┐
              │    MCP TOOLBOX          │
              │    (Executable)         │
              │                         │
              │  MCP Tools Available:   │
              │  • get_all_patients     │
              │  • get_critical_patients│
              │  • get_patients_by_risk │
              │  • get_patient_by_id    │
              │  • query_by_diagnosis   │
              │  • list_collections     │
              └────────┬────────────────┘
                       │
                       │ Firestore SDK
                       ▼
    ┌─────────────────────────────────────────────────────┐
    │                                                       │
    │           GOOGLE CLOUD FIRESTORE                     │
    │       (Database: careflow-478811/careflow-db)        │
    │                                                       │
    │  Collections:                                        │
    │  • /patients                    [Main patient data] │
    │    └─ /interactions             [Call logs]         │
    │    └─ /medicationLog            [Med tracking]      │
    │  • /alerts                      [Active alerts]     │
    │  • /users                       [Healthcare staff]  │
    │                                                       │
    └──────────────────┬────────────────────────────────────┘
                       │
                       │ Real-time Sync (onSnapshot)
                       │
                       ▼
    ┌─────────────────────────────────────────────────────┐
    │                                                       │
    │           NEXT.JS FRONTEND (Vercel)                  │
    │                                                       │
    │  ┌──────────────────────────────────────────────┐   │
    │  │           NextAuth Authentication            │   │
    │  │     (Role-based: Nurse/Coordinator/Admin)    │   │
    │  └──────────────────┬───────────────────────────┘   │
    │                     │                                │
    │  ┌──────────────────▼───────────────────────────┐   │
    │  │         Dashboard Pages (App Router)         │   │
    │  │                                              │   │
    │  │  /dashboard     → Overview & KPIs           │   │
    │  │  /patients      → Patient List              │   │
    │  │  /patient/{id}  → Patient Detail & History  │   │
    │  │  /alerts        → Critical Alert Management │   │
    │  │  /config        → System Configuration      │   │
    │  └──────────────────────────────────────────────┘   │
    │                                                       │
    └───────────────────────────────────────────────────────┘
                       ▲
                       │
              ┌────────┴─────────┐
              │                  │
         ┌────▼────┐       ┌─────▼─────┐
         │  NURSE  │       │COORDINATOR│
         │  Sarah  │       │  Michael  │
         └─────────┘       └───────────┘
```

**Key Architectural Principles:**

1. **Dual-Agent Specialization**: Separate agents for voice interaction (Caller) and medical intelligence (Pulse)
2. **MCP Protocol**: Standardized toolbox integration for Firestore database access
3. **A2A Protocol**: Inter-agent communication using JSON-RPC + SSE streaming
4. **Voice-First Interface**: Natural phone conversations via Twilio ConversationRelay + ElevenLabs
5. **Real-Time Sync**: Firestore acts as the single source of truth with live updates to frontend
6. **Containerized Deployment**: Both agents run as separate Cloud Run services
7. **Cloud-Native**: Leverages managed Google Cloud services for scalability and reliability

---

### **2.2. Technology Stack**

#### **Frontend (Next.js Application)**

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | Next.js | 16.0.3 | React-based full-stack framework with App Router |
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
| **CareFlow Pulse Agent** | Google ADK | 1.6.1+ | Medical reasoning agent with MCP toolbox integration |
| **CareFlow Caller Agent** | LangGraph | Latest | Voice interface agent with REACT architecture |
| **Language** | Python | 3.10-3.12 | Backend logic for both agents |
| **AI Model** | Gemini 2.5 Flash | Latest | Fast, intelligent LLM for medical triage and conversation |
| **MCP Protocol** | toolbox-core | Latest | Model Context Protocol for Firestore database access |
| **A2A Protocol** | a2a-sdk | Latest | Agent-to-Agent communication (JSON-RPC + SSE) |
| **Voice Interface** | Twilio ConversationRelay | Latest | Real-time voice streaming with WebSocket |
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

### **2.3. Component Interaction Flow**

This section describes the typical request flow through the system for key scenarios.

#### **Flow 1: Scheduled Patient Follow-Up Call**

```
1. Cloud Scheduler (8:15 AM)
   │
   ├─→ POST /api/careflow/trigger-scheduled-calls
   │   Body: { "timeSlot": "morning", "hour": 8 }
   │
2. CareFlow-Main Agent (Vertex AI)
   │
   ├─→ Query Firestore: Get patients with medications at 8am
   │   WHERE dischargePlan.medications[].scheduleHour == 8
   │
3. For each patient:
   │
   ├─→ CareFlow-Connect Agent
   │   │
   │   ├─→ Generate Dynamic Prompt (patient context + safety rules)
   │   │
   │   └─→ Twilio Voice API: Initiate call
   │       │
   │       └─→ Connect to Deepgram for conversation
   │
4. Patient answers, conversation happens
   │
5. Deepgram sends webhook with transcript
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
    │  │  • Model: Gemini 2.5 Flash                       │   │
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
    │  ┌──────────────────┐         ┌──────────────────┐       │
    │  │  Twilio          │         │  Deepgram        │       │
    │  │  • Voice calls   │         │  • STT/TTS       │       │
    │  │  • SMS gateway   │         │  • Conversation  │       │
    │  │  • Webhooks      │         │  • Barge-in      │       │
    │  └──────────────────┘         └──────────────────┘       │
    └────────────────────────────────────────────────────────────┘
```

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
6. **UUID Primary Keys**: Patients use UUIDs for universal uniqueness (future: may support hospital MRN)

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
| `name` | `string` | ✅ | Patient's full name | `"Sarah Mitchell"` | PHI - encrypted at rest |
| `dateOfBirth` | `Timestamp` | ✅ | Date of birth for age calculation | `Timestamp(1978-03-15)` | PHI |
| `contact` | `Map` | ✅ | Contact information object | See below | PHI |
| `dischargePlan` | `Map` | ✅ | Medical discharge context | See below | Critical for AI prompt generation |
| `riskLevel` | `string` | ✅ | Current patient risk classification | `"GREEN"` | Enum: `GREEN`, `ORANGE`, `RED` - **Indexed** |
| `lastAssessmentDate` | `Timestamp` | ✅ | When risk was last evaluated | `Timestamp(2025-11-15 08:20)` | Updated after each interaction |
| `alert` | `Map` or `null` | ⚠️ | Active alert object (null if no alert) | See below | Only present for ORANGE/RED patients |
| `assignedNurse` | `Map` | ✅ | Primary nurse coordinator | See below | For handover and notifications |
| `aiBrief` | `string` | ❌ | Latest AI-generated summary | `"Patient stable, no concerns"` | Generated by CareFlow-Brief agent |
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
| `agentName` | `string` | ❌ | Which ADK agent handled this | `"CareFlow-Analyze"` | For debugging |
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
  "agentName": "CareFlow-Analyze",
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

### **3.9. Data Migration & Seeding**

For development and testing, you'll need to seed the database with mock data.

#### **Seed Script (TypeScript)**

```typescript
// scripts/seedFirestore.ts
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, doc, setDoc, Timestamp } from 'firebase/firestore';

const seedPatients = async () => {
  const db = getFirestore();
  
  const patientData = {
    patientId: "550e8400-e29b-41d4-a716-446655440000",
    name: "Sarah Mitchell",
    dateOfBirth: Timestamp.fromDate(new Date('1978-03-15')),
    contact: {
      phone: "+15551234567",
      email: "sarah.mitchell@email.com",
      preferredMethod: "voice"
    },
    dischargePlan: {
      dischargeDate: Timestamp.fromDate(new Date('2025-11-10')),
      diagnosis: "Post-operative cardiac surgery (CABG)",
      dischargingPhysician: "Dr. Emily Rodriguez",
      hospitalId: "HOSP001",
      medications: [
        {
          name: "Aspirin",
          dosage: "81mg",
          frequency: "Once daily at 8:00 AM",
          scheduleHour: 8,
          startDate: Timestamp.now()
        }
      ],
      criticalSymptoms: ["chest pain", "shortness of breath"],
      warningSymptoms: ["swelling", "fatigue"]
    },
    riskLevel: "GREEN",
    lastAssessmentDate: Timestamp.now(),
    alert: null,
    assignedNurse: {
      userId: "user_nurse_sarah_123",
      name: "Sarah Johnson, RN",
      phone: "+15559876543",
      email: "sarah.johnson@hospital.com"
    },
    createdAt: Timestamp.now(),
    updatedAt: Timestamp.now(),
    status: "active"
  };
  
  await setDoc(doc(db, 'patients', patientData.patientId), patientData);
  console.log('✅ Seeded patient:', patientData.name);
};

seedPatients().catch(console.error);
```

**Run with:**
```bash
npx tsx scripts/seedFirestore.ts
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
│                   CareFlow-Main (Orchestrator)              │
│                                                               │
│  Responsibilities:                                           │
│  • Receives external triggers (webhooks, scheduler)          │
│  • Routes requests to specialized agents                     │
│  • Manages Firestore synchronization                         │
│  • Coordinates multi-step workflows                          │
│  • Error handling and fallback logic                         │
└───────────┬───────────────┬─────────────────┬───────────────┘
            │               │                 │
            │               │                 │
    ┌───────▼──────┐ ┌─────▼────────┐ ┌──────▼──────────┐
    │  CareFlow-   │ │  CareFlow-   │ │   CareFlow-     │
    │   Connect    │ │   Analyze    │ │     Brief       │
    └──────────────┘ └──────────────┘ └─────────────────┘
```

#### **Deployment Platform: Vertex AI Agent Engine**

All agents are packaged together and deployed as a single **ADK App** to Vertex AI Agent Engine:

- **Serverless**: No infrastructure management required
- **Auto-scaling**: Automatically scales from 0 to N instances based on traffic
- **Built-in Monitoring**: Integrated with Cloud Logging and Cloud Trace
- **API Endpoints**: Exposes REST endpoints for external triggers
- **Authentication**: Uses Google Cloud IAM for secure access

**Deployment Command:**
```bash
cd app/
make deploy
# Or manually:
uv run python -m app.agent_engine_app deploy
```

This command:
1. Packages all agent code and dependencies
2. Uploads to Google Cloud Storage (staging bucket)
3. Deploys to Vertex AI Agent Engine in `us-central1`
4. Creates/updates the Agent Engine endpoint
5. Returns the publicly accessible API URL

---

### **4.2. Agent: `CareFlow-Main` (Orchestrator)**

**Role:** The orchestrator is the entry point for all external interactions. It receives webhook calls, scheduler triggers, and routes work to specialized agents.

**File:** `app/agent.py` (root_agent)

#### **Responsibilities**

| Responsibility | Description | Tools Used |
| :--- | :--- | :--- |
| **Webhook Handling** | Receives POST requests from Twilio, Deepgram, and Cloud Scheduler | N/A (HTTP endpoint) |
| **Request Routing** | Determines which specialized agent should handle the request | ADK planner |
| **Firestore Sync** | All database reads/writes go through this agent | `firestore_tool` |
| **Workflow Coordination** | Manages multi-step processes (e.g., call → analyze → update → alert nurse) | ADK session management |
| **Error Recovery** | Handles failures and retries | Try/catch + logging |

#### **Key Configuration**

```python
# app/agent.py
from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner
from app.config import config

root_agent = LlmAgent(
    name=config.internal_agent_name,  # "careflow_pulse_agent"
    model=config.model,                 # "gemini-2.5-flash"
    description="AI agent that monitors post-hospitalization patients",
    planner=BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(include_thoughts=True)
    ),
    instruction="""
    You are CareFlow Pulse, an AI-powered patient monitoring orchestrator.
    
    Your job is to:
    1. Receive triggers from external systems (scheduler, Twilio webhooks)
    2. Route work to specialized agents (Connect, Analyze, Brief)
    3. Synchronize all state changes to Firestore
    4. Ensure no patient interaction is lost
    
    Always prioritize patient safety. When in doubt, escalate to human nurses.
    """,
    output_key="patient_monitoring",
)
```

#### **Example Workflow**

**Scenario:** Cloud Scheduler triggers morning calls at 8:15 AM

```python
# Orchestrator receives webhook
POST /api/careflow/trigger-scheduled-calls
Body: { "timeSlot": "morning", "hour": 8 }

# 1. Query Firestore for patients
patients = firestore_tool.query(
    collection='patients',
    where=[
        ('status', '==', 'active'),
        ('dischargePlan.medications', 'array-contains', {'scheduleHour': 8})
    ]
)

# 2. For each patient, delegate to CareFlow-Connect
for patient in patients:
    connect_agent.initiate_call(
        patient_id=patient['patientId'],
        patient_name=patient['name'],
        medications=patient['dischargePlan']['medications'],
        critical_symptoms=patient['dischargePlan']['criticalSymptoms']
    )

# 3. Wait for call completion webhook
# 4. Delegate analysis to CareFlow-Analyze
# 5. Update Firestore with results
# 6. If RED alert, delegate to CareFlow-Brief for summary
```

---

### **4.3. Agent: `CareFlow-Connect` (Connector)**

**Role:** Generates dynamic, context-rich prompts for voice interactions and initiates outbound communication (voice calls or SMS).

**File:** `app/agent.py` (specialized agent, invoked by orchestrator)

#### **Responsibilities**

| Responsibility | Description | Output |
| :--- | :--- | :--- |
| **Dynamic Prompt Generation** | Creates a unique system prompt for each patient call | String (prompt) |
| **Patient Context Injection** | Includes patient name, diagnosis, medications, critical symptoms | Part of prompt |
| **Safety Rules Encoding** | Embeds "Safe Handover Protocol" and critical keyword detection | Part of prompt |
| **Call Initiation** | Triggers Twilio Voice API to call patient | Twilio Call SID |
| **SMS Sending** | Sends text messages when voice is unavailable | Twilio Message SID |

#### **Dynamic Prompt Template**

The CareFlow-Connect agent must generate a unique prompt for each patient call that includes:

**Required Elements in Prompt:**
1. **Patient Identification**: Name, diagnosis, discharge date
2. **Medication List**: All medications scheduled for this time slot with dosages and frequencies
3. **Critical Symptoms**: List from `dischargePlan.criticalSymptoms` that trigger immediate escalation
4. **Safe Handover Protocol**: Exact script to use if patient mentions critical symptoms or asks for medical advice
5. **Conversation Goals**: Check medication adherence, assess symptoms, provide reassurance
6. **Conversation Style Guidelines**: Warm, empathetic, simple language, avoid medical jargon

**Prompt Structure:**
- Role definition: "You are CareFlow, a friendly AI assistant..."
- Patient context section with medical history
- Today's medication checklist
- Critical alert keywords (dynamically inserted from Firestore)
- Handover script: "Thank you for telling me that... I'm alerting your nurse now..."
- Example opening greeting

**Tools Invoked:**
- `twilio_voice_call`: Initiates call to patient's phone number, connects to Deepgram with generated prompt
- `twilio_sms_sender`: Sends text message as fallback if voice call fails or patient prefers SMS

---

### **4.4. Agent: `CareFlow-Analyze` (Medical Triage)**

**Role:** Analyzes patient responses (voice transcripts or SMS text) to classify risk level and determine if escalation is needed.

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
4. Invoke CareFlow-Brief agent to generate detailed summary
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

### **4.5. Agent: `CareFlow-Brief` (Synthesis)**

**Role:** Generates concise, actionable summaries for nurses when a RED or ORANGE alert is triggered. This is the "AI Brief" that appears on the dashboard.

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

#### **Tool 1: `firestore_tool`**

**Purpose:** Read and write data to Firestore

**Operations:**
- `query(collection, filters)`: Query documents with where clauses, returns list of documents
- `get(collection, doc_id)`: Retrieve single document by ID
- `update(collection, doc_id, data)`: Update existing document fields
- `create(collection, data)`: Create new document with auto-generated ID
- `delete(collection, doc_id)`: Delete document (use with caution)

**Authentication:** Uses Google Cloud service account credentials configured in ADK deployment

#### **Tool 2: `twilio_voice_call`**

**Purpose:** Initiate outbound voice calls via Twilio

**Parameters:**
- `to`: Patient phone number in E.164 format (+15551234567)
- `from_`: Twilio phone number
- `twiml`: TwiML instructions (XML) or URL to Deepgram webhook
- `status_callback`: Webhook URL for call status updates

**Returns:** Twilio Call SID (unique identifier for tracking)

**Configuration Required:**
- Twilio Account SID
- Twilio Auth Token
- Purchased Twilio phone number

#### **Tool 3: `twilio_sms_sender`**

**Purpose:** Send SMS messages to patients

**Parameters:**
- `to`: Patient phone number
- `body`: Message text (max 160 characters recommended)
- `status_callback`: Webhook URL for delivery status

**Returns:** Twilio Message SID

#### **Tool 4: `deepgram_voice_agent_connector`**

**Purpose:** Connect Twilio call audio stream to Deepgram for AI-powered conversation

**Implementation Method:** Generate TwiML with `<Stream>` verb that connects to Deepgram WebSocket endpoint

**Parameters Passed to Deepgram:**
- `model`: Deepgram model (e.g., "nova-2")
- `language`: Language code (e.g., "en-US")
- `prompt`: Dynamic conversation prompt generated by CareFlow-Connect

**Return:** TwiML XML string to be used by Twilio

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
   - Invoke CareFlow-Connect agent to generate dynamic prompt
   - Initiate Twilio voice call with Deepgram connection
   - Log outbound call in `/patients/{id}/interactions` with type `OUTBOUND_CALL`

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
   - Pass SMS body to CareFlow-Analyze agent
   - Determine if message indicates:
     - Medication adherence confirmation (keywords: "yes", "took", "done")
     - Symptom report (keywords from critical/warning symptom lists)
     - Request for help (keywords: "help", "question", "call me")

4. **Update Firestore:**
   - Log interaction in `/patients/{id}/interactions` with type `INBOUND_SMS`
   - If medication confirmed, create entry in `/medicationLog` with status `taken`
   - If symptoms reported, invoke CareFlow-Analyze for risk classification
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

**Purpose:** Webhook endpoint for Deepgram and Twilio to POST voice call results, including full conversation transcripts and call status.

#### **Request Specification**

**HTTP Method:** `POST`

**Headers:**
- `Content-Type: application/json`
- `X-Deepgram-Signature: {signature}` (for webhook validation)

**Request Body Schema:**

| Field | Type | Required | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `callSid` | `string` | ✅ | Twilio call identifier | `"CA1234567890abcdef"` |
| `patientPhone` | `string` | ✅ | Patient's phone number | `"+15551234567"` |
| `callStatus` | `string` | ✅ | Final call status | `"completed"`, `"no-answer"`, `"busy"`, `"failed"` |
| `callDuration` | `number` | ❌ | Call duration in seconds | `180` (null if not completed) |
| `transcript` | `string` | ❌ | Full conversation transcript | `"Agent: Hello Sarah... Patient: I have chest pain..."` |
| `criticalAlertTriggered` | `boolean` | ✅ | If Deepgram detected critical keyword during call | `true` or `false` |
| `timestamp` | `string` | ✅ | ISO 8601 timestamp | `"2025-11-15T08:20:45.123Z"` |

**Example Request (Completed Call):**
```json
{
  "callSid": "CA1234567890abcdef",
  "patientPhone": "+15551234567",
  "callStatus": "completed",
  "callDuration": 180,
  "transcript": "Agent: Good morning Sarah, this is CareFlow checking in on your recovery. How are you feeling today?\nPatient: Not good. I have chest pain and I'm dizzy.\nAgent: Thank you for telling me that, Sarah. For your safety, I'm alerting your nurse coordinator now.",
  "criticalAlertTriggered": true,
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
  "criticalAlertTriggered": false,
  "timestamp": "2025-11-15T08:16:30.456Z"
}
```

#### **Processing Logic**

1. **Identify Patient:**
   - Query Firestore `/patients` where `contact.phone == {patientPhone}`
   - If not found, log error and return 200 (avoid Deepgram retries)

2. **Handle Call Status:**
   
   **If `callStatus == "completed"` and transcript exists:**
   - Log interaction in `/patients/{id}/interactions` with type `OUTBOUND_CALL`
   - Include full transcript and call duration
   - Invoke CareFlow-Analyze agent to classify risk from transcript
   - If `criticalAlertTriggered == true`, immediately escalate to RED alert
   - Update Firestore patient document with analysis results
   - If RED/ORANGE, invoke CareFlow-Brief to generate summary
   - If RED, call assigned nurse via Twilio
   
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

#### **Webhook Validation**

Validate Deepgram signature using:
1. Deepgram API key (secret)
2. HMAC-SHA256 of request body
3. Compare with `X-Deepgram-Signature` header

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

#### **Deepgram Webhook Security**

**Method:** API key validation or signature verification

**Configuration:**
- Store Deepgram API key as secret in Google Secret Manager
- Validate `X-Deepgram-Signature` header on incoming webhooks
- Reject requests without valid signature

---

### **5.6. Rate Limiting & Security**

#### **Rate Limiting Strategy**

**Cloud Scheduler Endpoints:**
- No explicit rate limiting needed (controlled by scheduler frequency)
- Expected traffic: 3 requests/day (morning, noon, evening)

**Webhook Endpoints (Twilio, Deepgram):**
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

