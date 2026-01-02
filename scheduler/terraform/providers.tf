# ============================================================================
# CAREFLOW PULSE - TERRAFORM PROVIDERS
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-02
# License: Proprietary - All Rights Reserved
#
# Description:
#   Google Cloud provider configuration with staging and production aliases.
#   Enables dual-environment deployment via for_each loops with separate
#   billing projects and regional configurations.
# ============================================================================

provider "google" {
  alias           = "staging"
  project         = var.staging_project_id
  region          = var.region
  billing_project = var.staging_project_id
}

provider "google" {
  alias           = "prod"
  project         = var.prod_project_id
  region          = var.region
  billing_project = var.prod_project_id
}
