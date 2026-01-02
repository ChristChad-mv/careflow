# ============================================================================
# CAREFLOW PULSE - TERRAFORM VARIABLES
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-02
# License: Proprietary - All Rights Reserved
#
# Description:
#   Input variables for Cloud Scheduler Terraform configuration.
#   Defines project IDs, regions, and CareFlow Pulse Agent URLs for
#   multi-environment deployment (staging + production).
# ============================================================================

# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================

variable "prod_project_id" {
  type        = string
  description = "GCP Project ID for production environment"
}

variable "staging_project_id" {
  type        = string
  description = "GCP Project ID for staging environment"
}

variable "project_name" {
  type        = string
  description = "Project name (used as prefix for resource names)"
  default     = "careflow"
}

# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================

variable "region" {
  type        = string
  description = "GCP Region for Cloud Scheduler"
  default     = "us-central1"
}

variable "pulse_agent_urls" {
  type        = map(string)
  description = "Map of CareFlow Pulse Agent Cloud Run service URLs by environment"
  default = {
    prod    = "https://careflow-agent-production-url.run.app"
    staging = "https://careflow-agent-staging-url.run.app"
  }
}

variable "pulse_agent_service_name" {
  type        = string
  description = "Name of the CareFlow Pulse Agent Cloud Run service"
  default     = "careflow-agent"
}
