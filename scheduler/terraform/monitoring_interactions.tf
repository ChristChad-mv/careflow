# ============================================================================
# CAREFLOW PULSE - FIRESTORE INTERACTIONS MONITORING (ADD-ON)
# ============================================================================
# Additional monitoring for the Firestore interactions subcollection.
# This ensures the retry system is working correctly by verifying that
# interactions are being logged to the subcollection after each call.

# Alert: No documents written to interactions subcollection in 30 minutes
resource "google_monitoring_alert_policy" "interactions_subcollection_empty" {
  for_each = local.deploy_project_ids

  project      = each.value
  display_name = "CareFlow - No Firestore Interactions Logged (30min)"
  combiner     = "OR"

  conditions {
    display_name = "Firestore interactions subcollection not written to"

    condition_threshold {
      # Monitor Firestore write operations to the interactions subcollection
      filter = join(" AND ", [
        "resource.type = \"firestore.googleapis.com/Database\"",
        "resource.labels.database_id = \"careflow-db\"",
        "metric.type = \"firestore.googleapis.com/document/write_count\"",
        "metric.label.op = \"CREATE\"",
        # Filter for interactions subcollection paths
        "resource.labels.database_id =~ \".*interactions.*\""
      ])

      duration        = "1800s" # 30 minutes
      comparison      = "COMPARISON_LT"
      threshold_value = 1

      aggregations {
        alignment_period     = "300s" # 5 min windows
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email_alerts[each.key].id]

  alert_strategy {
    auto_close = "86400s" # 24 hours
  }

  documentation {
    content   = <<-EOT
      ## CareFlow Interactions Subcollection Not Updated

      **Severity:** CRITICAL
      
      **Description:** 
      No documents have been written to the Firestore `interactions` subcollection in the last 30 minutes.
      This means the retry system's idempotency mechanism is BROKEN.
      
      **Impact:**
      - Patients will be called MULTIPLE times (duplicates)
      - Retry logic cannot filter out already-contacted patients
      - `get_pending_patients` will always return all patients
      
      **Root Causes:**
      1. `log_patient_interaction` tool not being called by the agent
      2. Firestore permissions issue preventing subcollection writes
      3. Agent failing silently after audio analysis
      4. System prompt missing MANDATORY instruction
      
      **Action Required (URGENT):**
      1. Check CareFlow Agent logs for `log_patient_interaction` calls
      2. Verify Firestore IAM permissions for subcollection writes
      3. Review System Prompt - ensure "log_patient_interaction" is MANDATORY
      4. Manually trigger test round and verify interaction log appears in Firestore
      
      **Test Command:**
      ```bash
      curl -X POST http://careflow-agent-url/trigger-rounds \
        -H "Content-Type: application/json" \
        -d '{"scheduleHour": 8}'
      ```
      
      Then check: Firestore → `patients/{patientId}/interactions`
      
      **Dashboards:**
      - [Firestore Metrics](https://console.cloud.google.com/firestore)
      - [CareFlow Agent Logs](https://console.cloud.google.com/run)
    EOT
    mime_type = "text/markdown"
  }

  depends_on = [
    google_project_service.monitoring_api,
    google_monitoring_notification_channel.email_alerts
  ]
}

# Additional log-based metric specifically for Python tool calls
resource "google_logging_metric" "interaction_logger_calls" {
  for_each = local.deploy_project_ids

  project = each.value
  name    = "careflow/interaction_logger_tool_calls"
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="careflow-agent"
    (
      jsonPayload.message=~"Logged interaction for patient" OR
      jsonPayload.message=~"log_patient_interaction" OR
      textPayload=~"log_patient_interaction"
    )
    severity="INFO"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"

    labels {
      key         = "patient_id"
      value_type  = "STRING"
      description = "Patient ID"
    }

    labels {
      key         = "schedule_slot"
      value_type  = "STRING"
      description = "Schedule slot"
    }
  }

  label_extractors = {
    "patient_id"    = "EXTRACT(jsonPayload.patient_id)"
    "schedule_slot" = "EXTRACT(jsonPayload.scheduleSlot)"
  }

  depends_on = [google_project_service.monitoring_api]
}
