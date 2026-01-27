# ============================================================================
# CAREFLOW MCP TOOLBOX - CLOUD RUN SERVICE CONFIGURATION
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Cloud Run service deployment for MCP Toolbox with multi-environment
#   support (staging/production).
# ============================================================================

# Get project information
data "google_project" "project" {
  for_each   = local.deploy_project_ids
  project_id = each.value
}

# Enable required APIs in deployment projects
resource "google_project_service" "deploy_project_services" {
  for_each = {
    for pair in setproduct(keys(local.deploy_project_ids), var.deploy_project_apis) :
    "${pair[0]}-${pair[1]}" => {
      project = local.deploy_project_ids[pair[0]]
      service = pair[1]
    }
  }

  project            = each.value.project
  service            = each.value.service
  disable_on_destroy = false
}

# Enable required APIs in CI/CD project
resource "google_project_service" "cicd_services" {
  for_each = toset(var.cicd_project_apis)

  project            = var.cicd_runner_project_id
  service            = each.value
  disable_on_destroy = false
}

# Cloud Run service for MCP Toolbox
resource "google_cloud_run_v2_service" "mcp_toolbox" {
  for_each = local.deploy_project_ids

  name                = "${var.project_name}-${each.key}"
  location            = var.region
  project             = each.value
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_ALL"

  labels = {
    "created-by" = "terraform"
    "component"  = "mcp-toolbox"
  }

  template {
    containers {
      # Official GENAI Toolbox image
      image = "us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest"

      args = [
        "serve",
        "--tools-file", "/etc/mcp/tools.yaml",
        "--address", "0.0.0.0",
        "--port", "8080"
      ]

      ports {
        container_port = 8080
        name           = "http1"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = each.value
      }

      env {
        name  = "FIRESTORE_DATABASE"
        value = var.firestore_database
      }

      # Mount the tools.yaml from Secret Manager
      volume_mounts {
        name       = "tools-config"
        mount_path = "/etc/mcp"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = false
        startup_cpu_boost = true
      }

      startup_probe {
        tcp_socket {
          port = 8080
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    volumes {
      name = "tools-config"
      secret {
        secret = google_secret_manager_secret.tools_config.secret_id
        items {
          version = "latest"
          path    = "tools.yaml"
        }
      }
    }

    service_account                  = google_service_account.mcp_sa[each.key].email
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  depends_on = [
    google_project_service.deploy_project_services,
    google_service_account.mcp_sa
  ]
}

# Allow unauthenticated access (internal service, adjust as needed)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  for_each = local.deploy_project_ids

  project  = each.value
  location = var.region
  name     = google_cloud_run_v2_service.mcp_toolbox[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
