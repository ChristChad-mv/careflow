# ============================================================================
# CAREFLOW MCP TOOLBOX - LOCAL VALUES CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Local values and computed variables for infrastructure deployment.
# ============================================================================

locals {
  deploy_project_ids = {
    prod    = var.prod_project_id
    staging = var.staging_project_id
  }

  artifact_registry_repository = "${var.region}-docker.pkg.dev/${var.cicd_runner_project_id}/${var.project_name}"
}
