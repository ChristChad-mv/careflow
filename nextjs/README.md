# 🏥 CareFlow Pulse - Frontend Dashboard

The command center for **CareFlow Pulse**, a production-grade healthcare monitoring system designed for the **Gemini 3 Hackathon**. This Next.js application provides nurse coordinators with real-time patient insights, clinical alerts, and a dedicated interactive demo mode.

---

## ✨ Features

### 📊 Real-time Clinical Dashboard
- **Patient Monitoring**: Track recovery status across the entire patient population.
- **Severity Triage**: Instant visualization of patients in `Safe`, `Warning`, or `Critical` states.
- **Resource Tracking**: Monitor nurse workload and active monitoring sessions.

### 🚨 Smart Alert System
- **Multimodal Intelligence**: View alerts triggered by Gemini 3 Pro analyzing native audio (Breathlessness, Alarms, Cognitive Fog).
- **Interactive Triage**: Acknowledge, escalate, or resolve clinical alerts directly from the dashboard.
- **Audit Logging**: Comprehensive, HIPAA-aligned interaction history for every patient.

### 🧪 Hackathon Demo Mode
- **Zero-to-Call in Seconds**: Specialized interface for judges to "Adopt a Scenario" and receive a live clinical call from the agent.
- **Instant Result Tracking**: Real-time feedback loop showing how the AI brain processes the call audio and updates the dashboard.

---

## 🛠 Tech Stack

- **Framework**: [Next.js 16](https://nextjs.org/) (App Router, Turbopack)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)
- **State & Real-time**: [Firebase Firestore](https://firebase.google.com/docs/firestore) + [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Auth**: [NextAuth.js](https://next-auth.js.org/)

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js (v20+ recommended)
- Firebase Project (Firestore enabled)

### 2. Environment Setup
Create a `.env.local` file in this directory with the following keys:
```bash
# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# Agent Connection
CAREFLOW_AGENT_URL=http://localhost:8000
```

### 3. Installation
```bash
npm install --legacy-peer-deps
```

### 4. Development Run
```bash
npm run dev
```
The app will be available at [http://localhost:3000](http://localhost:3000).

---

## 🏗 Architecture

The frontend acts as the **A2UI (Agent-to-UI)** bridge in our Ecosystem:
1. **Pulse Agent** updates Firestore collections directly via MCP.
2. **Next.js Dashboard** listens to real-time snapshots from Firestore.
3. **Demo API** (`/api/demo/trigger`) sends JSON-RPC messages to the agents to initiate outbound calls.

---

## 🌍 Deployment

Optimized for **Vercel**:
1. Connect your GitHub repository.
2. Set Environment Variables in the Vercel Dashboard.
3. Deploy!

---
