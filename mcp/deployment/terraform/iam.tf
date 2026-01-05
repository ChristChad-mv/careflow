# ============================================================================
# CAREFLOW MCP TOOLBOX - IAM CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   IAM roles and permissions for service accounts and Cloud Run services.
# ============================================================================

# Grant MCP Toolbox service account required roles
resource "google_project_iam_member" "mcp_sa_roles" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), var.app_sa_roles) :
    join(",", pair) => {
      project = local.deploy_project_ids[pair[0]]
      role    = pair[1]
    }
  }

  project = each.value.project
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.mcp_sa[split(",", each.key)[0]].email}"

  depends_on = [google_project_service.deploy_project_services]
}

# Grant CI/CD service account roles in CI/CD project
resource "google_project_iam_member" "cicd_project_roles" {
  for_each = toset(var.cicd_roles)

  project = var.cicd_runner_project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cicd_runner_sa.email}"

  depends_on = [google_project_service.cicd_services]
}

# Grant CI/CD service account deployment roles in staging/prod
resource "google_project_iam_member" "cicd_deploy_roles" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), var.cicd_sa_deployment_required_roles) :
    "${pair[0]}-${pair[1]}" => {
      project_id = local.deploy_project_ids[pair[0]]
      role       = pair[1]
    }
  }

  project = each.value.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.cicd_runner_sa.email}"

  depends_on = [google_project_service.deploy_project_services]
}

# Allow Cloud Run to pull images from Artifact Registry
resource "google_project_iam_member" "artifact_registry_reader" {
  for_each = local.deploy_project_ids

  project = var.cicd_runner_project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:service-${data.google_project.project[each.key].number}@serverless-robot-prod.iam.gserviceaccount.com"

  depends_on = [google_project_service.cicd_services]
}

# Allow CI/CD SA to create tokens
resource "google_service_account_iam_member" "cicd_token_creator" {
  service_account_id = google_service_account.cicd_runner_sa.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.cicd_runner_sa.email}"
}
