# HIPAA Compliance Technical Guide

## 1. Overview

CareFlow Pulse is designed to be HIPAA compliant by leveraging Google Cloud Platform's BAA-covered services (Firestore) and implementing the "Shared Responsibility" requirements at the application layer.

## 2. Technical Implementation

### 2.1 Access Control (The Fortress)

- **Mechanism:** Firestore Security Rules (`firestore.rules`).
- **Policy:** Strict Row-Level Security (RLS).
- **Rule:** Users can ONLY read/write patients belonging to their `hospitalId`.
- **Enforcement:** Database kernel level (cannot be bypassed by Frontend).

### 2.2 Audit Controls (Audit Trails)

- **Mechanism:** `AuditService` (`src/lib/audit.ts`).
- **Policy:** All PHI mutations are logged.
- **Scope:** `WRITE` actions on `Patient` and `Alert` resources.
- **Storage:** Dedicated `audit_logs` collection.
- **Immutability:** Protected by Firestore Rules (`allow update, delete: if false`).

### 2.3 Integrity & Validation

- **Mechanism:** Zod Schemas (`src/lib/schemas.ts`).
- **Policy:** Strict strict input validation.
- **Prevention:** Blocks "Mass Assignment" attacks (e.g., unauthorized hospital hopping).

### 2.4 Transmission Security

- **Mechanism:** TLS 1.2+ (via Vercel/Google Cloud defaults).
- **Policy:** HSTS Enabled in `next.config.ts`.
- **Headers:** Strict Content Security Policy (CSP) configured.

### 2.5 AI Defense in Depth (Model Armor)

- **Component:** Google Model Armor.
- **Function:** Real-time sanitation of Inputs (Prompts) and Outputs (Model Responses).
- **Policy: Fail-Closed Security.** The system is configured to block interactions if the Model Armor API is unavailable or returns an error, ensuring zero exposure to unvetted content.
- **Protection 1 (Input/Attack Surface):** Analyzes incoming prompts to block **Prompt Injection**, **Jailbreak attempts**, and **Adversarial inputs** designed to bypass safety filters or manipulate the clinical persona.
- **Protection 2 (Output/Data Leakage):** Applies a secondary **PHI/PII Sanitization** layer (DLP) on all model responses. This ensures that even if the model attempts to hallucinate or leak sensitive data (like MRNs, names, or unmasked history), the output is blocked or redacted before reaching the user.
- **Protection 3 (Safety):** Filters for Toxic content, Hate speech, and other harmful categories to ensure professional clinical interaction.

## 3. Operations Manual

### Verification Procedure

1. **Audit Logs:** Navigate to Firestore Console -> `audit_logs`. Verify new entries appear after patient updates.
2. **Access:** Try to read a patient from a different Hospital ID (Should return Permission Denied).

## 4. Disaster Recovery

- **Backup:** Firestore Point-in-Time Recovery (PITR) should be enabled in Google Cloud Console.
