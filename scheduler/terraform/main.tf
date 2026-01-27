# ============================================================================
# CAREFLOW PULSE - CLOUD SCHEDULER CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-02
# License: Proprietary - All Rights Reserved
#
# Description:
#   Terraform configuration for Cloud Scheduler orchestrating daily patient
#   rounds. Deploys to staging and production environments simultaneously
#   using for_each pattern with OIDC authentication.
# ============================================================================
# This Terraform configuration deploys Cloud Scheduler jobs to orchestrate
# daily patient rounds across the CareFlow Pulse ecosystem.
#
# Architecture:
# - Cloud Scheduler triggers the CareFlow Pulse Agent (orchestrator)
# - CareFlow Pulse Agent uses A2A protocol to delegate to Caller Agent
# - Caller Agent makes voice calls via Twilio ConversationRelay
#
# Deployment:
# - Deploys to BOTH staging and production environments
# - Uses for_each loop with local.deploy_project_ids
#
# Jobs (per environment):
# - Morning rounds: 8:15 AM EST
# - Noon rounds: 12:15 PM EST
# - Evening rounds: 8:15 PM EST
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.13.0"
    }
  }
}

# ============================================================================
# LOCALS
# ============================================================================

locals {
  deploy_project_ids = {
    prod = var.prod_project_id
    # staging = var.staging_project_id
  }
}

# ============================================================================
# ENABLE REQUIRED APIS
# ============================================================================

resource "google_project_service" "scheduler_apis" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), ["cloudscheduler.googleapis.com", "run.googleapis.com", "iam.googleapis.com"]) :
    "${pair[0]}_${replace(pair[1], ".", "_")}" => {
      project = local.deploy_project_ids[pair[0]]
      service = pair[1]
    }
  }

  project            = each.value.project
  service            = each.value.service
  disable_on_destroy = false
}

# ============================================================================
# SERVICE ACCOUNT FOR CLOUD SCHEDULER
# ============================================================================

resource "google_service_account" "scheduler_sa" {
  for_each = local.deploy_project_ids

  account_id   = "${var.project_name}-${each.key}-scheduler"
  display_name = "CareFlow Cloud Scheduler Service Account"
  description  = "Service account used by Cloud Scheduler to trigger CareFlow agent endpoints"
  project      = each.value

  depends_on = [google_project_service.scheduler_apis]
}

# Grant Cloud Run Invoker role to scheduler SA
resource "google_cloud_run_v2_service_iam_member" "pulse_agent_invoker" {
  for_each = local.deploy_project_ids

  project  = each.value
  location = var.region
  name     = var.pulse_agent_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa[each.key].email}"

  depends_on = [google_service_account.scheduler_sa]
}

# ============================================================================
# JOB 1: MORNING ROUNDS (8:00 AM Paris)
# ============================================================================

resource "google_cloud_scheduler_job" "morning_rounds" {
  for_each = local.deploy_project_ids

  name             = "${var.project_name}-${each.key}-morning-rounds"
  description      = "CareFlow Pulse - Morning patient rounds for medication adherence"
  schedule         = "0 8 * * *"
  time_zone        = "Europe/Paris"
  attempt_deadline = "600s"
  project          = each.value
  region           = var.region

  retry_config {
    retry_count          = 3
    max_retry_duration   = "0s"
    min_backoff_duration = "60s"
    max_backoff_duration = "300s"
  }

  http_target {
    http_method = "POST"
    uri         = var.pulse_agent_urls[each.key]

    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      jsonrpc = "2.0"
      method  = "message/stream"
      id      = "scheduler-job"
      params = {
        message = {
          messageId = "scheduler-morning-rounds"
          kind      = "message"
          role      = "user"
          parts = [{
            kind = "text"
            text = "start daily rounds for 8:00"
          }]
          metadata = {
            source       = "cloud-scheduler"
            scheduleHour = 8
            environment  = each.key
          }
        }
      }
    }))

    oidc_token {
      service_account_email = google_service_account.scheduler_sa[each.key].email
      audience              = var.pulse_agent_urls[each.key]
    }
  }

  depends_on = [
    google_project_service.scheduler_apis,
    google_service_account.scheduler_sa,
    # google_cloud_run_v2_service_iam_member.pulse_agent_invoker
  ]
}

# ============================================================================
# JOB 2: NOON ROUNDS (DISABLED)
# ============================================================================

# resource "google_cloud_scheduler_job" "noon_rounds" {
#   for_each = local.deploy_project_ids
# 
#   name             = "${var.project_name}-${each.key}-noon-rounds"
#   description      = "CareFlow Pulse - Noon patient rounds for medication adherence"
#   schedule         = "15 12 * * *"
#   time_zone        = "America/New_York"
#   attempt_deadline = "600s"
#   project          = each.value
#   region           = var.region
# 
#   retry_config {
#     retry_count          = 3
#     max_retry_duration   = "0s"
#     min_backoff_duration = "60s"
#     max_backoff_duration = "300s"
#   }
# 
#   http_target {
#     http_method = "POST"
#     uri         = var.pulse_agent_urls[each.key]
# 
#     headers = {
#       "Content-Type" = "application/json"
#     }
# 
#     body = base64encode(jsonencode({
#       scheduleHour = 12
#       timezone     = "America/New_York"
#       triggerType  = "scheduled"
#       source       = "cloud-scheduler"
#       environment  = each.key
#     }))
# 
#     oidc_token {
#       service_account_email = google_service_account.scheduler_sa[each.key].email
#       audience              = var.pulse_agent_urls[each.key]
#     }
#   }
# 
#   depends_on = [
#     google_project_service.scheduler_apis,
#     google_service_account.scheduler_sa,
#     # google_cloud_run_v2_service_iam_member.pulse_agent_invoker
#   ]
# }

# ============================================================================
# JOB 3: EVENING ROUNDS (DISABLED)
# ============================================================================

# resource "google_cloud_scheduler_job" "evening_rounds" {
#   for_each = local.deploy_project_ids
# 
#   name             = "${var.project_name}-${each.key}-evening-rounds"
#   description      = "CareFlow Pulse - Evening patient rounds for medication adherence"
#   schedule         = "15 20 * * *"
#   time_zone        = "America/New_York"
#   attempt_deadline = "600s"
#   project          = each.value
#   region           = var.region
# 
#   retry_config {
#     retry_count          = 3
#     max_retry_duration   = "0s"
#     min_backoff_duration = "60s"
#     max_backoff_duration = "300s"
#   }
# 
#   http_target {
#     http_method = "POST"
#     uri         = var.pulse_agent_urls[each.key]
# 
#     headers = {
#       "Content-Type" = "application/json"
#     }
# 
#     body = base64encode(jsonencode({
#       scheduleHour = 20
#       timezone     = "America/New_York"
#       triggerType  = "scheduled"
#       source       = "cloud-scheduler"
#       environment  = each.key
#     }))
# 
#     oidc_token {
#       service_account_email = google_service_account.scheduler_sa[each.key].email
#       audience              = var.pulse_agent_urls[each.key]
#     }
#   }
# 
#   depends_on = [
#     google_project_service.scheduler_apis,
#     google_service_account.scheduler_sa,
#     # google_cloud_run_v2_service_iam_member.pulse_agent_invoker
#   ]
# }
