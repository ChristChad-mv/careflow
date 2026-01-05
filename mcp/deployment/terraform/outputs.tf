# ============================================================================
# CAREFLOW MCP TOOLBOX - TERRAFORM OUTPUTS
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Output values from infrastructure deployment for use in other modules
#   and for reference.
# ============================================================================

output "mcp_toolbox_urls" {
  description = "URLs of deployed MCP Toolbox Cloud Run services"
  value = {
    for env, project_id in local.deploy_project_ids :
    env => google_cloud_run_v2_service.mcp_toolbox[env].uri
  }
}

output "mcp_service_accounts" {
  description = "Service account emails for MCP Toolbox"
  value = {
    for env in keys(local.deploy_project_ids) :
    env => google_service_account.mcp_sa[env].email
  }
}

output "cicd_service_account" {
  description = "CI/CD runner service account email"
  value       = google_service_account.cicd_runner_sa.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for MCP Toolbox images"
  value       = local.artifact_registry_repository
}
