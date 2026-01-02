# ============================================================================
# CAREFLOW PULSE - TERRAFORM OUTPUTS
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-02
# License: Proprietary - All Rights Reserved
#
# Description:
#   Output values from Cloud Scheduler Terraform deployment.
#   Returns service account emails, job names, and job IDs organized
#   by environment (staging/prod) for use in monitoring and operations.
# ============================================================================

# ============================================================================
# SERVICE ACCOUNT OUTPUTS
# ============================================================================

output "scheduler_service_account_emails" {
  description = "Map of Cloud Scheduler service account emails by environment"
  value = {
    for k, v in google_service_account.scheduler_sa : k => v.email
  }
}

# ============================================================================
# SCHEDULER JOB OUTPUTS
# ============================================================================

output "morning_rounds_job_names" {
  description = "Map of morning rounds job names by environment"
  value = {
    for k, v in google_cloud_scheduler_job.morning_rounds : k => v.name
  }
}

output "noon_rounds_job_names" {
  description = "Map of noon rounds job names by environment"
  value = {
    for k, v in google_cloud_scheduler_job.noon_rounds : k => v.name
  }
}

output "evening_rounds_job_names" {
  description = "Map of evening rounds job names by environment"
  value = {
    for k, v in google_cloud_scheduler_job.evening_rounds : k => v.name
  }
}

output "all_job_ids" {
  description = "Map of all Cloud Scheduler job IDs by environment and time"
  value = {
    for env in keys(local.deploy_project_ids) : env => {
      morning = google_cloud_scheduler_job.morning_rounds[env].id
      noon    = google_cloud_scheduler_job.noon_rounds[env].id
      evening = google_cloud_scheduler_job.evening_rounds[env].id
    }
  }
}

output "job_schedules" {
  description = "Human-readable schedule information"
  value = {
    morning = "8:15 AM EST daily"
    noon    = "12:15 PM EST daily"
    evening = "8:15 PM EST daily"
  }
}
