# ============================================================================
# CAREFLOW MCP TOOLBOX - SERVICE ACCOUNTS CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Service accounts for MCP Toolbox and CI/CD pipeline execution.
# ============================================================================

# Service account for MCP Toolbox runtime
resource "google_service_account" "mcp_sa" {
  for_each = local.deploy_project_ids

  project      = each.value
  account_id   = "${var.project_name}-sa"
  display_name = "MCP Toolbox Service Account (${each.key})"
  description  = "Service account for MCP Toolbox Cloud Run service with Firestore access"

  depends_on = [google_project_service.deploy_project_services]
}

# Service account for CI/CD runner
resource "google_service_account" "cicd_runner_sa" {
  project      = var.cicd_runner_project_id
  account_id   = "${var.project_name}-cicd-sa"
  display_name = "MCP Toolbox CI/CD Runner"
  description  = "Service account for CI/CD pipeline to build and deploy MCP Toolbox"

  depends_on = [google_project_service.cicd_services]
}
