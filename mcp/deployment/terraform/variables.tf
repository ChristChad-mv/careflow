# ============================================================================
# CAREFLOW MCP TOOLBOX - TERRAFORM VARIABLES
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Input variables for MCP Toolbox infrastructure deployment.
# ============================================================================

variable "project_name" {
  type        = string
  description = "Project name used as a base for resource naming"
  default     = "careflow-mcp-toolbox"
}

variable "prod_project_id" {
  type        = string
  description = "**Production** Google Cloud Project ID for resource deployment."
}

variable "staging_project_id" {
  type        = string
  description = "**Staging** Google Cloud Project ID for resource deployment."
}

variable "cicd_runner_project_id" {
  type        = string
  description = "Google Cloud Project ID where CI/CD pipelines will execute."
}

variable "region" {
  type        = string
  description = "Google Cloud region for resource deployment."
  default     = "us-central1"
}

variable "host_connection_name" {
  description = "Name of the host connection to create in Cloud Build"
  type        = string
  default     = "careflow-mcp-github-connection"
}

variable "repository_name" {
  description = "Name of the repository you'd like to connect to Cloud Build"
  type        = string
}

variable "firestore_database" {
  type        = string
  description = "Firestore database name to connect to"
  default     = "careflow-db"
}

variable "app_sa_roles" {
  description = "List of roles to assign to the MCP toolbox service account"
  type        = list(string)
  default = [
    "roles/datastore.user",           # Read/write Firestore
    "roles/logging.logWriter",        # Write logs
    "roles/cloudtrace.agent",         # Send traces
  ]
}

variable "cicd_roles" {
  description = "List of roles to grant to the CI/CD runner service account for the CI/CD project"
  type        = list(string)
  default = [
    "roles/cloudbuild.builds.editor",
    "roles/cloudbuild.workerPoolUser",
    "roles/iam.serviceAccountUser",
    "roles/run.developer",
    "roles/artifactregistry.admin",
    "roles/storage.admin",
    "roles/secretmanager.secretAccessor",
  ]
}

variable "cicd_sa_deployment_required_roles" {
  description = "List of roles required by the CI/CD service account to deploy to staging and production projects"
  type        = list(string)
  default = [
    "roles/run.developer",
    "roles/iam.serviceAccountUser",
  ]
}

variable "deploy_project_apis" {
  description = "List of Google Cloud APIs to enable in staging and production projects"
  type        = list(string)
  default = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
  ]
}

variable "cicd_project_apis" {
  description = "List of Google Cloud APIs to enable in the CI/CD runner project"
  type        = list(string)
  default = [
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
  ]
}
