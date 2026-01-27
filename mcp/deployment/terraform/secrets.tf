# ============================================================================
# CAREFLOW MCP TOOLBOX - SECRET MANAGER CONFIGURATION
# ============================================================================

resource "google_secret_manager_secret" "tools_config" {
  secret_id = "mcp-tools-config"
  project   = var.prod_project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "tools_config_version" {
  secret      = google_secret_manager_secret.tools_config.id
  secret_data = file("${path.module}/../../tools.yaml")
}

# Grant access to the secret for the MCP service account
resource "google_secret_manager_secret_iam_member" "mcp_sa_secret_access" {
  for_each  = local.deploy_project_ids
  project   = each.value
  secret_id = google_secret_manager_secret.tools_config.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_sa[each.key].email}"
}
