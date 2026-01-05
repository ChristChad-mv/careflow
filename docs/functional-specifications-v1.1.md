# **CareFlow Pulse: Functional Specifications (v2.0)**

| | |
| :--- | :--- |
| **Document Version:** | 2.0 |
| **Date:** | 2026-01-04 |
| **Status:** | **Draft** |
| **Author:** | Christ |

---

### **Revision History**
| Version | Date | Author | Changes |
| :--- | :--- | :--- | :--- |
| 1.0 | 2025-12-20 | Christ | Initial Draft |
| 1.1 | 2025-12-22 | Christ | Incorporated feedback on handover protocol. |
| 2.0 | 2025-12-24 | Christ | Comprehensive rewrite: Added Mission, Personas, and detailed User Stories. Expanded all sections for clarity. |
| 3.0 | 2026-01-04 | AI Team | Updated Architecture (Agent-driven Alerts), Added 4 Detailed Clinical Scenarios (COPD, Knee, Heart Failure, AMI). |

## 1. Introduction: The Vision for Proactive Post-Hospitalization Care

### 1.1. The Problem: The Revolving Door of Hospital Readmissions

In today's healthcare landscape, the 30 days following a patient's discharge from the hospital are a critical and vulnerable period. A significant percentage of patients are readmitted within this window, leading to poorer health outcomes, immense stress for patients and their families, and billions of dollars in costs to the healthcare system.

Nurse coordinators are on the front lines of this battle, tasked with monitoring dozens, if not hundreds, of recently discharged patients. This manual process is often overwhelming, inefficient, and prone to human error. Critical warning signs can be missed in the noise of routine check-ins, and nurses spend valuable time on stable patients instead of focusing on those who are most at-risk.

### 1.2. The Solution: CareFlow Pulse

**CareFlow Pulse** is an AI-powered, proactive monitoring system designed to serve as a dedicated, intelligent assistant for nurse coordinators. Our mission is to **break the cycle of hospital readmissions** by automating routine patient follow-ups and intelligently triaging alerts, ensuring that human expertise is applied precisely where it is needed most.

The system is not just a tool; it is designed to be an empathetic and integrated member of the care team. It communicates with patients in a natural, helpful manner and delivers clear, concise, and actionable insights to healthcare professionals, transforming post-hospitalization care from a reactive chore into a proactive, life-saving process.

#### **High-Level Solution Architecture**

```mermaid
graph TD
    %% Actors
    Patient((Patient))
    Nurse((Nurse Coordinator))

    %% System Components
    subgraph "CareFlow Pulse System"
        Scheduler[Cloud Scheduler]
        
        subgraph "AI Agent Fleet"
            PulseAgent[CareFlow Pulse Agent<br/>(Central Intelligence & Data)]
            CallerAgent[CareFlow Caller Agent<br/>(Voice Interface)]
        end
        
        Database[(Firestore Database)]
        Dashboard[Nurse Dashboard]
    end

    %% Flow
    Scheduler -->|Trigger Daily Rounds| PulseAgent
    PulseAgent -->|Retrieve Plans| Database
    PulseAgent -->|Task: Call Patient| CallerAgent
    CallerAgent <-->|Voice Call| Patient
    
    CallerAgent -->|Transcript & Analysis| PulseAgent
    
    Note over PulseAgent: Analyzes Risk<br/>Creates Alerts
    
    PulseAgent -->|Update Risk & Alerts| Database
    Database -->|Real-time Sync| Dashboard
    
    Dashboard -->|View Alerts| Nurse
    Nurse -->|Manual Intervention| Patient
    
    %% Styling
    style Patient fill:#e1f5fe,stroke:#01579b
    style Nurse fill:#e1f5fe,stroke:#01579b
    style PulseAgent fill:#f3e5f5,stroke:#4a148c
    style CallerAgent fill:#f3e5f5,stroke:#4a148c
    style Dashboard fill:#e8f5e9,stroke:#1b5e20
    style Database fill:#fff3e0,stroke:#e65100
```

### 1.3. Scope of the System

- **In Scope:** Automated, scheduled patient follow-ups via Voice; analysis of patient responses; automated risk classification (Green/Yellow/Red); real-time dashboard for nurses; alert management.
- **Out of Scope (for v1.0):** Direct integration with Electronic Health Record (EHR) systems; billing and insurance processing.

---

## 2. User Personas

### 2.1. Persona: The Nurse Coordinator
- **Name:** Sarah, RN
- **Role:** Post-Discharge Care Coordinator
- **Goals:** Prevent readmissions, ensure patients adhere to their care plans, and focus her limited time on the most critical cases.
- **Workflow:** primarily interacts with the **Dashboard**, responding to alerts created by the CareFlow Agent.

### 2.2. Patient Personas (See Scenarios below)
Patients recently discharged with various conditions (COPD, Orthopedic Surgery, Heart Failure, AMI) requiring different levels of monitoring.

---

## 3. Detailed Clinical Scenarios & System Behavior

This section outlines four specific scenarios demonstrating how CareFlow Pulse handles different risk levels and patient interactions. In all cases, the **CareFlow Agent** performs the interview, analyzes the result, and **automatically creates the alert** on the dashboard for Sarah to review.

### 3.1. Scenario 1: The "Green Path" - Stable COPD Patient
*Automated Success, No Disturbance for Nurse*

**Patient:** **Robert (ID: 101)**
- **Diagnosis:** Chronic Obstructive Pulmonary Disease (COPD)
- **Status:** Stable

**Process:**
1.  **Agent Call:** The CareFlow Caller Agent calls Robert.
    - *Agent:* "Good morning Robert. How is your breathing today?"
    - *Robert:* "It's good, about the same as yesterday. No trouble."
    - *Agent:* "Are you using your inhalers as prescribed?"
    - *Robert:* "Yes, I used the morning one."
    - *Agent:* "Any coughing or changes in mucus?"
    - *Robert:* "No changes."
2.  **Analysis:** The Agent determines Robert is following his plan and symptoms are baseline.
3.  **Result:**
    - Risk Level set to **GREEN**.
    - Interaction logged in Dashboard.
    - **Nurse Action:** None required. Sarah sees the green checkmark on her list and knows Robert is fine.

### 3.2. Scenario 2: The "Yellow Path" - Total Knee Replacement (Education Gap)
*Warning - Requires Human Verification*

**Patient:** **Christine (ID: 102)**
- **Diagnosis:** Total Knee Replacement
- **Status:** Confused about medication and appointments.

**Process:**
1.  **Agent Call:**
    - *Agent:* "Hello Christine. Are you managing your pain medication okay?"
    - *Christine:* "I think so... was I supposed to take the white pill twice or three times? And I forgot when my physio appointment is."
    - *Agent:* "According to your discharge plan, the white pill (Tramadol) is every 6 hours as needed. And your physio is scheduled for Thursday at 2 PM. Do you have a pen to write that down?"
    - *Christine:* "Oh, thank you. Thursday at 2."
2.  **Analysis:**
    - The Agent successfully provided information, BUT detects a risk of non-adherence due to confusion.
    - It decides this warrants a "human triple-check."
3.  **Result:**
    - Risk Level set to **YELLOW**.
    - **Alert Created:** "Patient confusion regarding meds and appointment. Re-education provided, but verify understanding."
    - **Nurse Action:** Sarah sees the **YELLOW** alert. She clicks "Take Ownership" and calls Christine personally to confirm she truly understands the plan. She listens to the Agent's call recording to hear exactly what confused Christine.

### 3.3. Scenario 3: The "Red Path" - Heart Failure Decompensation
*Critical Alert - Urgent Medical Intervention*

**Patient:** **Maria (ID: 103)**
- **Diagnosis:** Congestive Heart Failure (CHF)
- **Status:** Deteriorating (Fluid Overload)

**Process:**
1.  **Agent Call:**
    - *Agent:* "Hello Maria. Have you weighed yourself this morning?"
    - *Maria:* "Yes... I've gained about 4 pounds since yesterday."
    - *Agent:* "I see. And how is your breathing?"
    - *Maria:* "I feel... a bit short of breath just walking to the kitchen."
    - *Agent:* "Do you have any swelling in your ankles?"
    - *Maria:* "Yes, they are very puffy."
2.  **Analysis:**
    - The Agent identifies specific "Red Flag" keywords for CHF: **Weight gain > 3lbs**, **Shortness of Breath**, **Edema**.
    - Determines immediate risk of readmission.
3.  **Result:**
    - Risk Level set to **RED**.
    - **Alert Created:** "CRITICAL: Signals of decompensation. Weight +4lbs, Dyspnea, Edema."
    - **Nurse Action:** The Dashboard flashes red for Maria. Sarah immediately sees the alert. She calls Maria to instruct her to increase her diuretic dosage (per standing orders) or come to the clinic, preventing a full ER admission.

### 3.4. Scenario 4: The "Red Path" - Acute Myocardial Infarction (AMI)
*Emergency - Immediate Action*

**Patient:** **Karl (ID: 104)**
- **Diagnosis:** Post-AMI (Heart Attack)
- **Status:** Emergency

**Process:**
1.  **Agent Call:**
    - *Agent:* "Hi Karl. checking in. Any chest pain today?"
    - *Karl:* "Yes... I have this heavy pressure in my chest again. It started 20 minutes ago."
    - *Agent:* "Is the pain radiating to your arm or jaw?"
    - *Karl:* "A little bit to my left arm."
2.  **Analysis:**
    - The Agent recognizes symptoms of a recurring heart attack.
    - **Immediate Protocol:** The Agent advises Karl to stay on the line or hang up and dial 911 (depending on configured protocol).
3.  **Result:**
    - Risk Level set to **RED (Emergency)**.
    - **Alert Created:** "EMERGENCY: Recurrent Chest Pain. Possible AMI."
    - **Nurse Action:** Sarah sees the emergency flag. She calls Karl immediately while coordinating with emergency services to ensure he gets to the ER.

---

## 4. Functional Requirements Deep Dive

### FS-1: Patient & Follow-up Lifecycle Management
| ID | Feature | Description |
| :--- | :--- | :--- |
| **FS-1.1** | **Session & Schedule** | System defines a schedule (e.g., D+1, D+3). At the scheduled time, the **CareFlow Pulse Agent** creates a task. |
| **FS-1.2** | **Automated Interview** | The **Caller Agent** conducts the interview using specific clinical protocols (Post-Discharge Call Document). |
| **FS-1.3** | **Agent-Driven Triage** | The **Agent** (not the Nurse) analyzes the transcript and sets the Risk: **GREEN** (Stable), **YELLOW** (Warning/Education needed), **RED** (Critical/symptoms). |
| **FS-1.4** | **Alert Generation** | The **Agent** automatically generates an Alert object in the database for any non-Green status, populating it with a summary of the issue. |

### FS-2: Nurse Coordinator Interface
| ID | Feature | Description |
| :--- | :--- | :--- |
| **FS-2.1** | **Real-Time Dashboard** | Displays patients sorted by Risk (Red top). Updates instantly when the Agent finishes a call. |
| **FS-2.2** | **"Take Ownership"** | Nurse Sarah clicks to acknowledge an alert. This changes the status from "New" to "In Progress," letting the team know she is handling it. |
| **FS-2.3** | **Audio & Transcript Access** | Nurse can replay the specific conversation segment where the patient reported the issue to verify context before calling. |

