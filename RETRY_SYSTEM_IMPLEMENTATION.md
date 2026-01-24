# CareFlow Pulse - Retry System Implementation Summary

## ✅ **Fichiers créés/modifiés :**

### 1. **Tools créés :**

- `careflow-agent/app/tools/interaction_logger.py` → Tool `log_patient_interaction` (subcollection)
- `careflow-agent/app/tools/retry_tools.py` → Tool `get_pending_patients` (Firestore SDK)
- `careflow-agent/app/app_utils/run_patient_rounds.py` → Orchestration logic
- `caller-agent/app/app_utils/retry_utils.py` → Cloud Tasks scheduling

### 2. **Serveurs modifiés :**

- `careflow-agent/app/server.py` → Endpoints `/trigger-rounds` et `/retry-rounds`
- `caller-agent/app/server.py` → Gestion `busy/no-answer` + Cloud Task

### 3. **Agent modifié :**

- `careflow-agent/app/agent.py` → Added `retry_tools` + `interaction_tools`

---

## 📝 **À AJOUTER AU SYSTEM PROMPT (system_prompts.py) :**

### **Après Workflow 1 (ligne ~85), ajouter :**

```python
### Workflow 1b: Retry Rounds (Smart Retry) 🔄
**Trigger:** Message starting with "RETRY TRIGGER:".
1.  **Extract Hour**: Parse schedule hour from message (e.g., "RETRY TRIGGER: 8:00" → 8).
2.  **Query Pending**: Call `get_pending_patients(scheduleHour, hospitalId="{HOSPITAL_ID}")`.
    - This tool returns ONLY patients WITHOUT logged interactions for this slot.
    - It's your smart retry filter - prevents duplicate calls!
3.  **Iterate & Call**: For EACH patient returned, call `send_remote_agent_task` (same as Workflow 1).
4.  **Report**: "Retry rounds initiated for X pending patients."
```

### **Modifier Workflow 2 (ligne ~96), CHANGER b. en :**

```python
b. `log_patient_interaction`: **CRITICAL FIRST**. Call `log_patient_interaction(patientId, content, callSid, scheduleSlot)`.
   - This MARKS the patient as contacted, enabling retry idempotency.
   - scheduleSlot format: "YYYY-MM-DD_HH" (e.g., "2026-01-23_08").
```

### **Ajouter section "Tools Checklist" (ligne ~28) :**

```python
**🛠️ AVAILABLE TOOLS UPDATED:**
1. `fetch_call_audio(call_sid)`: Downloads recording.
2. `get_pending_patients(scheduleHour, hospitalId)`: **NEW** - Returns only uncontacted patients for retry.
3. `log_patient_interaction(patientId, content, callSid, scheduleSlot)`: **NEW** - Logs to subcollection (MANDATORY after analysis).
4. `update_patient_risk(...)`: Updates dashboard.
5. `create_alert(...)`: Creates nurse alerts.
```

---

## 🔧 **Comment tester :**

### **Test 1 : Rounds initiaux**

```bash
cd scheduler
python3 run_daily_job.py  # Triggers 8:00 rounds
```

### **Test 2 : Retry (15min plus tard simulé)**

```bash
curl -X POST http://localhost:8080/retry-rounds \
  -H "Content-Type: application/json" \
  -d '{"scheduleHour": 8, "scheduleSlot": "2026-01-23_08"}'
```

### **Test 3 : Vérifier interactions loggées**

→ Check Firestore : `patients/{patientId}/interactions` collection

---

## 📊 **Monitoring Email (TODO) :**

À ajouter dans `scheduler/terraform/monitoring.tf` :

```hcl
resource "google_monitoring_alert_policy" "interactions_missing" {
  display_name = "CareFlow - No Interactions Logged After 30min"
  combiner     = "OR"
  
  conditions {
    display_name = "No interactions in subcollection"
    condition_threshold {
      filter          = "resource.type=\"firestore.googleapis.com/Database\" AND metric.type=\"firestore.googleapis.com/document/read_count\" AND resource.label.database_id=\"careflow-db\""
      duration        = "1800s"  # 30 minutes
      comparison      = "COMPARISON_LT"
      threshold_value = 1
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "86400s"  # 24h
  }
}

resource "google_monitoring_notification_channel" "email" {
  display_name = "CareFlow DevOps Email"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}
```

**Variables nécessaires :**

```hcl
variable "alert_email" {
  description = "Email for monitoring alerts"
  type        = string
  default     = "devops@careflow.com"
}
```

---

## ⚡ **Architecture finale :**

```
Cloud Scheduler (8:00)
    ↓
/trigger-rounds
    ├→ 200 OK (immediate)
    ├→ asyncio: trigger_agent_rounds() ← Agent fetches + calls
    │   ↓
    │   send_remote_agent_task → Caller → Twilio
    │   ↓
    │   completed? → log_patient_interaction ✅ (IDEMPOTENCY)
    │
    └→ asyncio: schedule_retry_task() ← Cloud Task @8:15
    
[15 min later]
Cloud Tasks → /retry-rounds
    ↓
get_pending_patients(8, HOSP001)  ← Firestore query
    ↓
Returns: [patients WITHOUT interactions]
    ↓
trigger_agent_rounds(retry_mode=True)
```

---

## 🎯 **Prochaines étapes :**

1. ✅ **Redémarrer les serveurs** (`uv run python server.py`)
2. ✅ **Tester le flow complet** (scheduler → retry)
3. ✅ **Vérifier Interactions dans Firestore**
4. ⏳ **Implémenter monitoring email** (Terraform)
5. ⏳ **Commit sur branche `feat/robust-retry-system`**
