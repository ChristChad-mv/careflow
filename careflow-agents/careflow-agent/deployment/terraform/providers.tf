# ============================================================================
# CAREFLOW PULSE AGENT - TERRAFORM PROVIDERS CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-02
# License: Proprietary - All Rights Reserved
#
# Description:
#   Terraform and Google Cloud provider configuration for CareFlow Pulse Agent
#   deployment infrastructure.
# ============================================================================

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.13.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.13.0"
    }
    github = {
      source  = "integrations/github"
      version = "~> 6.5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7.0"
    }
  }
}

provider "google" {
  alias                 = "staging_billing_override"
  billing_project       = var.staging_project_id
  region                = var.region
  user_project_override = true
}

provider "google" {
  alias                 = "prod_billing_override"
  billing_project       = var.prod_project_id
  region                = var.region
  user_project_override = true
}
