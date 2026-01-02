# ============================================================================
# CAREFLOW PULSE - CLOUD SCHEDULER CONFIGURATION
# ============================================================================
# Configuration file for Cloud Scheduler Terraform variables.
# Deploys to BOTH staging and production environments.
#
# Usage:
#   terraform apply -var-file=vars/env.tfvars
# ============================================================================

# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================

prod_project_id    = "careflow-478811"
staging_project_id = "careflow-staging-xxxxx"
project_name       = "careflow"

# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================

region = "us-central1"

pulse_agent_urls = {
  prod    = "https://careflow-agent-production-xxxxx.run.app"
  staging = "https://careflow-agent-staging-xxxxx.run.app"
}

pulse_agent_service_name = "careflow-agent"
