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

## 3. Operations Manual

### Verification Procedure
1. **Audit Logs:** Navigate to Firestore Console -> `audit_logs`. Verify new entries appear after patient updates.
2. **Access:** Try to read a patient from a different Hospital ID (Should return Permission Denied).

## 4. Disaster Recovery
- **Backup:** Firestore Point-in-Time Recovery (PITR) should be enabled in Google Cloud Console.
