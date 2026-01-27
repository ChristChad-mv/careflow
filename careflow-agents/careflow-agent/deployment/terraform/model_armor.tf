# ============================================================================
# CAREFLOW PULSE AGENT - MODEL ARMOR CONFIGURATION
# ============================================================================

resource "google_model_armor_template" "default" {
  provider = google-beta
  for_each = local.deploy_project_ids

  project     = each.value
  location    = "us"
  template_id = "default"

  filter_config {}

  depends_on = [google_project_service.deploy_project_services]
}
