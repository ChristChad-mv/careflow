# CareFlow Pulse - Cloud Scheduler Terraform

## 📋 Overview

This Terraform configuration deploys **Cloud Scheduler jobs** to orchestrate daily patient rounds for the CareFlow Pulse ecosystem. The scheduler triggers the CareFlow Pulse Agent at predetermined times, which then delegates voice calls to the Caller Agent via A2A protocol.

## 🏗️ Architecture

```
Cloud Scheduler (Morning/Noon/Evening)
    ↓ HTTPS POST + OIDC Auth
CareFlow Pulse Agent (Cloud Run)
    ↓ A2A Protocol (JSON-RPC + SSE)
CareFlow Caller Agent (Cloud Run)
    ↓ Twilio ConversationRelay
Patient Phone Calls
```

### Daily Schedule (EST)
- **Morning Rounds**: 8:15 AM
- **Noon Rounds**: 12:15 PM  
- **Evening Rounds**: 8:15 PM

## 📁 File Structure

```
scheduler/terraform/
├── main.tf          # Core Scheduler resources (255 lines)
├── variables.tf     # Input variables (58 lines)
├── outputs.tf       # Output values (69 lines)
├── providers.tf     # Google Cloud provider config (20 lines)
└── vars/
    └── env.tfvars   # Variable values (30 lines)
```

## 🚀 Deployment

### Prerequisites
```bash
# Install Terraform
sudo snap install terraform

# Authenticate with GCP
gcloud auth application-default login
```

### Step 1: Configure Variables
Edit `vars/env.tfvars` with your actual values:

```terraform
# Project IDs
prod_project_id    = "careflow-478811"
staging_project_id = "careflow-staging-12345"
project_name       = "careflow"

# Region
region = "us-central1"

# CareFlow Pulse Agent URLs (from Cloud Run deployment)
pulse_agent_urls = {
  prod    = "https://careflow-agent-abc123-uc.a.run.app"
  staging = "https://careflow-agent-xyz789-uc.a.run.app"
}

# Cloud Run service name
pulse_agent_service_name = "careflow-agent"
```

### Step 2: Initialize Terraform
```bash
cd scheduler/terraform
terraform init
```

### Step 3: Review Plan
```bash
terraform plan -var-file=vars/env.tfvars
```

This will show resources to be created:
- **6 API enablements** (3 APIs × 2 environments)
- **2 Service Accounts** (1 per environment)
- **2 IAM bindings** (Cloud Run Invoker roles)
- **6 Scheduler Jobs** (3 jobs × 2 environments)

**Total: 16 resources**

### Step 4: Apply Configuration
```bash
terraform apply -var-file=vars/env.tfvars
```

Confirm with `yes` when prompted.

## 📊 Outputs

After successful deployment:

```bash
terraform output

# Example output:
scheduler_service_account_emails = {
  prod    = "careflow-scheduler@careflow-478811.iam.gserviceaccount.com"
  staging = "careflow-scheduler@careflow-staging-12345.iam.gserviceaccount.com"
}

morning_rounds_job_names = {
  prod    = "careflow-morning-rounds"
  staging = "careflow-morning-rounds"
}

all_job_ids = {
  prod = {
    morning = "projects/careflow-478811/locations/us-central1/jobs/careflow-morning-rounds"
    noon    = "projects/careflow-478811/locations/us-central1/jobs/careflow-noon-rounds"
    evening = "projects/careflow-478811/locations/us-central1/jobs/careflow-evening-rounds"
  }
  staging = { ... }
}
```

## 🔍 Verification

### Check Scheduler Jobs
```bash
# List all jobs (prod)
gcloud scheduler jobs list --project=careflow-478811

# Describe specific job
gcloud scheduler jobs describe careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1
```

### Trigger Manual Test
```bash
# Force run morning job (prod)
gcloud scheduler jobs run careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1

# Check logs
gcloud logging read "resource.type=cloud_scheduler_job" \
  --project=careflow-478811 \
  --limit=20 \
  --format=json
```

## 🛠️ Operations

### Pause All Jobs
```bash
# Pause prod jobs
for job in careflow-morning-rounds careflow-noon-rounds careflow-evening-rounds; do
  gcloud scheduler jobs pause $job \
    --project=careflow-478811 \
    --location=us-central1
done
```

### Resume All Jobs
```bash
# Resume prod jobs
for job in careflow-morning-rounds careflow-noon-rounds careflow-evening-rounds; do
  gcloud scheduler jobs resume $job \
    --project=careflow-478811 \
    --location=us-central1
done
```

### View Job Execution History
```bash
# Last 10 executions
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_id=careflow-morning-rounds" \
  --project=careflow-478811 \
  --limit=10 \
  --format="table(timestamp,jsonPayload.message)"
```

## 🔐 Security

### OIDC Authentication
Each scheduler job authenticates to Cloud Run using **OIDC tokens** signed by the scheduler service account:

```terraform
oidc_token {
  service_account_email = google_service_account.scheduler_sa[each.key].email
  audience              = var.pulse_agent_urls[each.key]
}
```

### IAM Roles
- **Cloud Scheduler SA**: `roles/run.invoker` on CareFlow Pulse Agent
- **Least Privilege**: Service account can ONLY invoke the specific Cloud Run service

## 🧪 Testing

### Test Individual Job
```bash
# Test morning job (staging)
gcloud scheduler jobs run careflow-morning-rounds \
  --project=careflow-staging-12345 \
  --location=us-central1

# Check Pulse Agent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=careflow-agent" \
  --project=careflow-staging-12345 \
  --limit=5 \
  --format=json | jq '.[] | select(.jsonPayload.source == "cloud-scheduler")'
```

### Verify Payload
The scheduler sends this JSON payload:
```json
{
  "scheduleHour": 8,
  "timezone": "America/New_York",
  "triggerType": "scheduled",
  "source": "cloud-scheduler",
  "environment": "prod"
}
```

## 📈 Monitoring

### Key Metrics to Monitor
1. **Job Success Rate**: % of successful executions
2. **Job Latency**: Time to complete HTTP request
3. **Retry Count**: Number of retries triggered
4. **Error Rate**: Failed requests to Pulse Agent

### Cloud Monitoring Dashboard
```bash
# Query job execution metrics
gcloud monitoring time-series list \
  --filter='metric.type="cloudscheduler.googleapis.com/job/attempt_count"' \
  --project=careflow-478811
```

## 🔄 Updates

### Change Schedule
Edit `main.tf` and modify the `schedule` field:
```terraform
resource "google_cloud_scheduler_job" "morning_rounds" {
  schedule = "15 9 * * *"  # Changed to 9:15 AM
  # ...
}
```

Then apply:
```bash
terraform apply -var-file=vars/env.tfvars
```

### Add New Job
Add a new resource block to `main.tf`:
```terraform
resource "google_cloud_scheduler_job" "afternoon_rounds" {
  for_each = local.deploy_project_ids
  
  name     = "${var.project_name}-afternoon-rounds"
  schedule = "15 15 * * *"  # 3:15 PM EST
  # ... (copy pattern from other jobs)
}
```

## 🗑️ Cleanup

### Destroy All Resources
```bash
terraform destroy -var-file=vars/env.tfvars
```

⚠️ **Warning**: This will delete ALL scheduler jobs in BOTH staging and production!

## 📚 Resources

- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [OIDC Authentication](https://cloud.google.com/run/docs/authenticating/service-to-service)
- [Cron Expression Syntax](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)

## 🤝 Related Components

- **CareFlow Pulse Agent**: `/careflow-agents/careflow-agent/`
- **CareFlow Caller Agent**: `/careflow-agents/caller-agent/`
- **Scheduler Test Script**: `/scheduler/run_daily_job.py`

---

**Last Updated**: January 2025  
**Terraform Version**: >= 1.0  
**Google Provider Version**: ~> 7.13.0
