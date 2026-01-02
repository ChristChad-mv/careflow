# Cloud Scheduler for CareFlow Pulse

This directory contains the **production Cloud Scheduler configuration** for orchestrating automated daily patient rounds via Terraform.

## 📁 Directory Structure

```
scheduler/
├── terraform/              # Production Cloud Scheduler Infrastructure
│   ├── main.tf            # Scheduler jobs (staging + prod)
│   ├── variables.tf       # Input variables (prod/staging project IDs)
│   ├── outputs.tf         # Output values (job names, SA emails)
│   ├── providers.tf       # Google Cloud provider aliases
│   └── vars/
│       └── env.tfvars     # Configuration values
├── run_daily_job.py       # ⚠️ TEST SCRIPT ONLY (disconnect resilience)
├── Makefile               # Terraform operation shortcuts
├── .gitignore             # Git exclusions
└── README.md              # This file
```

## ⚠️ Important Distinction

**`run_daily_job.py` is NOT the production scheduler!**  

- **Purpose**: Test script for disconnect resilience testing
- **Environment**: Local development only (`localhost:8001`)
- **Usage**: Validates agent continues processing after client disconnect

For **production deployment**, use the **Terraform configuration** which provides:
- ✅ OIDC authentication (no API keys)
- ✅ Multi-environment deployment (staging + prod)
- ✅ Automatic retries with exponential backoff
- ✅ Cloud Monitoring & alerting integration
- ✅ IAM least-privilege security model

---

## 🏗️ Architecture Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE CLOUD SCHEDULER                          │
│      (Managed by Terraform - deploys to staging + prod)     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Morning      │  │ Noon         │  │ Evening      │     │
│  │ 8:15 AM EST  │  │ 12:15 PM EST │  │ 8:15 PM EST  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          │   HTTPS POST with OIDC Token       │
          └─────────────────┼──────────────────┘
                            ▼
          ┌────────────────────────────────────┐
          │  CareFlow Pulse Agent (Cloud Run)  │
          │  - Validates OIDC token            │
          │  - Queries Firestore for patients  │
          │  - Filters by schedule preferences │
          └──────────────┬─────────────────────┘
                         │
                         │ A2A Protocol (JSON-RPC + SSE)
                         ▼
          ┌────────────────────────────────────┐
          │  CareFlow Caller Agent (Cloud Run) │
          │  - Makes voice calls via Twilio    │
          │  - Streams audio with ElevenLabs   │
          │  - Logs interactions to Firestore  │
          └────────────────────────────────────┘
                         │
                         │ Twilio API
                         ▼
          ┌────────────────────────────────────┐
          │         Patient Phones             │
          └────────────────────────────────────┘
```

### Schedule Configuration

| Job Name | Time (EST) | Cron | Purpose |
|----------|------------|------|---------|
| `careflow-morning-rounds` | 8:15 AM | `15 8 * * *` | Post-breakfast medication adherence |
| `careflow-noon-rounds` | 12:15 PM | `15 12 * * *` | Mid-day symptom check |
| `careflow-evening-rounds` | 8:15 PM | `15 20 * * *` | Evening medication & review |

**Timezone**: `America/New_York` (automatic DST handling)

**Why 15 minutes past the hour?**  
- Avoids peak Cloud Scheduler load (on-the-hour spikes)
- Reduces Cloud Run cold start probability
- Gives patients time to settle after meals

---

## 🔐 Security Architecture

### Authentication Flow

```
1. Cloud Scheduler → Generates OIDC token signed by scheduler SA
                  ↓
2. Cloud Run      → Validates token audience & issuer
                  ↓
3. ✅ Authorized  → Request processed by Pulse Agent
```

### IAM Configuration

- **Service Account**: `careflow-scheduler@{project}.iam.gserviceaccount.com`
- **IAM Role**: `roles/run.invoker` on CareFlow Pulse Agent service
- **Principle**: Least privilege - can ONLY invoke the specific Cloud Run service

### Request Payload

Cloud Scheduler sends this JSON to the Pulse Agent:

```json
{
  "scheduleHour": 8,
  "timezone": "America/New_York",
  "triggerType": "scheduled",
  "source": "cloud-scheduler",
  "environment": "prod"
}
```

The Pulse Agent then:
1. Queries Firestore for active patients with matching schedule preferences
2. Delegates voice calls to Caller Agent via A2A protocol
3. Logs execution metadata to Firestore

---

## 🚀 Deployment Guide

### Prerequisites

1. **CareFlow Pulse Agent** deployed to Cloud Run
   ```bash
   cd careflow-agents/careflow-agent
   make deploy
   ```

2. **CareFlow Caller Agent** deployed to Cloud Run
   ```bash
   cd careflow-agents/caller-agent
   make deploy
   ```

3. **Terraform installed** (>= 1.0)
   ```bash
   sudo snap install terraform
   ```

4. **GCP Authentication**
   ```bash
   gcloud auth application-default login
   ```

### Step 1: Configure Variables

```bash
cd scheduler/terraform

# Edit configuration with your actual values
nano vars/env.tfvars
```

**Configuration example**:
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
terraform init
```

This downloads the Google Cloud provider (~7.13.0) and initializes the backend.

### Step 3: Preview Changes

```bash
terraform plan -var-file=vars/env.tfvars
```

**Expected resources** (16 total):
- **6 API Enablements** (`cloudscheduler.googleapis.com`, `run.googleapis.com`, `iam.googleapis.com` × 2 environments)
- **2 Service Accounts** (`careflow-scheduler` for staging + prod)
- **2 IAM Bindings** (Cloud Run Invoker roles)
- **6 Cloud Scheduler Jobs** (3 times × 2 environments)

### Step 4: Deploy

```bash
terraform apply -var-file=vars/env.tfvars
```

Type `yes` when prompted. Deployment takes ~2-3 minutes.

### Step 5: Verify

```bash
# List all scheduler jobs
gcloud scheduler jobs list --project=careflow-478811 --location=us-central1

# View specific job details
gcloud scheduler jobs describe careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1
```

**Expected output**:
```
name: projects/careflow-478811/locations/us-central1/jobs/careflow-morning-rounds
schedule: 15 8 * * *
state: ENABLED
timeZone: America/New_York
httpTarget:
  uri: https://careflow-agent-abc123-uc.a.run.app
  httpMethod: POST
  oidcToken:
    serviceAccountEmail: careflow-scheduler@careflow-478811.iam.gserviceaccount.com
```

---

## 🧪 Testing

### Local Development Testing

The `run_daily_job.py` script tests **disconnect resilience** during local development:

```bash
# Start local CareFlow Pulse Agent on port 8001
cd careflow-agents/careflow-agent
make run

# In another terminal, test disconnect resilience
cd ../../scheduler
python3 run_daily_job.py --hour 8   # Test morning rounds
python3 run_daily_job.py --hour 12  # Test noon rounds
python3 run_daily_job.py --hour 20  # Test evening rounds
```

The script intentionally disconnects after 10 seconds to verify the agent continues processing calls despite client disconnect.

### Manual Production Trigger

```bash
# Force trigger morning rounds (doesn't wait for 8:15 AM)
gcloud scheduler jobs run careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1

# View scheduler execution logs
gcloud logging read "resource.type=cloud_scheduler_job \
  AND resource.labels.job_id=careflow-morning-rounds" \
  --project=careflow-478811 \
  --limit=10 \
  --format=json
```

### Verify Agent Response

```bash
# Check Cloud Run logs from Pulse Agent
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=careflow-agent \
  AND jsonPayload.source=\"cloud-scheduler\"" \
  --project=careflow-478811 \
  --limit=20
```

Look for log entries like:
```json
{
  "severity": "INFO",
  "jsonPayload": {
    "message": "Scheduled rounds triggered",
    "source": "cloud-scheduler",
    "scheduleHour": 8,
    "patientsQueried": 45,
    "callsInitiated": 42
  }
}
```

---

## 🛠️ Operations

### Pause Jobs (Maintenance Mode)

```bash
# Pause all jobs in production
for job in morning-rounds noon-rounds evening-rounds; do
  gcloud scheduler jobs pause careflow-$job \
    --project=careflow-478811 \
    --location=us-central1
done
```

### Resume After Maintenance

```bash
# Resume all jobs
for job in morning-rounds noon-rounds evening-rounds; do
  gcloud scheduler jobs resume careflow-$job \
    --project=careflow-478811 \
    --location=us-central1
done
```

### Update Schedule Time

To change execution time (e.g., move morning rounds to 9:00 AM):

1. **Edit `terraform/main.tf`**:
   ```terraform
   resource "google_cloud_scheduler_job" "morning_rounds" {
     for_each = local.deploy_project_ids
     
     schedule = "0 9 * * *"  # Changed from 15 8 * * *
     # ...
   }
   ```

2. **Apply changes**:
   ```bash
   cd terraform/
   terraform apply -var-file=vars/env.tfvars
   ```

### View Execution History

```bash
# Last 20 executions with status
gcloud scheduler jobs describe careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1 \
  --format="table(state, lastAttemptTime, scheduleTime, status.code, status.message)"
```

---

## 📊 Monitoring & Alerting

### Key Metrics

Monitor these in **Cloud Console → Monitoring**:

1. **Job Success Rate**
   - Metric: `cloudscheduler.googleapis.com/job/attempt_count`
   - **Alert**: Failure rate > 5% over 1 hour

2. **Job Execution Duration**
   - Metric: `cloudscheduler.googleapis.com/job/execution_duration`
   - **Alert**: Duration > 5 minutes consistently

3. **Retry Frequency**
   - Query scheduler logs for `severity=ERROR`
   - **Alert**: > 10% retry rate

4. **Agent Response Time**
   - Cloud Run metric: `run.googleapis.com/request_latencies`
   - **Alert**: p95 latency > 30 seconds

### Create Alert Policy

```bash
# Alert on 3 consecutive failures
gcloud alpha monitoring policies create \
  --display-name="CareFlow Scheduler Failures" \
  --condition-display-name="3 consecutive job failures" \
  --notification-channels=YOUR_CHANNEL_ID \
  --condition-threshold-value=3 \
  --condition-threshold-duration=600s \
  --condition-filter='resource.type="cloud_scheduler_job" AND metric.type="cloudscheduler.googleapis.com/job/attempt_count"'
```

### Dashboard Queries

**Successful vs Failed Executions (Last 7 days)**:
```sql
fetch cloud_scheduler_job
| metric 'cloudscheduler.googleapis.com/job/attempt_count'
| filter resource.job_id =~ 'careflow-.*-rounds'
| group_by [resource.job_id, metric.response_class], 1d, [sum(value.attempt_count)]
| every 1d
```

---

## 🚨 Troubleshooting

### Issue: Jobs Not Executing

**Symptoms**: No logs, scheduler status shows `ENABLED` but no executions

**Diagnosis**:
```bash
# 1. Check job configuration
gcloud scheduler jobs describe careflow-morning-rounds \
  --project=careflow-478811 \
  --location=us-central1

# 2. Verify service account exists
gcloud iam service-accounts describe \
  careflow-scheduler@careflow-478811.iam.gserviceaccount.com

# 3. Check IAM binding
gcloud run services get-iam-policy careflow-agent \
  --region=us-central1 \
  --project=careflow-478811
```

**Solution**: Re-apply Terraform to fix IAM bindings:
```bash
terraform apply -var-file=vars/env.tfvars
```

---

### Issue: Jobs Failing with 403 Forbidden

**Symptoms**: Logs show `Permission denied` or `403 Forbidden`

**Diagnosis**:
```bash
# Check if IAM binding was created
terraform state list | grep iam_member

# Verify Cloud Run allows authenticated invocations
gcloud run services describe careflow-agent \
  --region=us-central1 \
  --project=careflow-478811 \
  --format="value(spec.template.metadata.annotations)"
```

**Solution**: Ensure service account has `roles/run.invoker`:
```bash
gcloud run services add-iam-policy-binding careflow-agent \
  --region=us-central1 \
  --project=careflow-478811 \
  --member="serviceAccount:careflow-scheduler@careflow-478811.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

### Issue: Jobs Timing Out

**Symptoms**: `DEADLINE_EXCEEDED` errors after 10 minutes

**Diagnosis**: Agent is processing too many patients sequentially

**Solutions**:
1. **Increase timeout** in `terraform/main.tf`:
   ```terraform
   resource "google_cloud_scheduler_job" "morning_rounds" {
     attempt_deadline = "1200s"  # 20 minutes instead of 10
   }
   ```

2. **Optimize agent processing**: Implement batch parallel processing in Pulse Agent

3. **Split patient batches**: Create multiple scheduler jobs for different patient cohorts

---

### Issue: Wrong Agent URL Configured

**Symptoms**: Jobs succeed but agent receives no requests

**Solution**: Update Cloud Run URL in `vars/env.tfvars` and re-apply:
```bash
nano terraform/vars/env.tfvars
# Update pulse_agent_urls.prod = "https://NEW-URL.run.app"

terraform apply -var-file=vars/env.tfvars
```

---

## �� Cost Analysis

### Cloud Scheduler Pricing

- **Jobs 1-3**: FREE (within Google Cloud free tier)
- **Jobs 4+**: $0.10/job/month

**For CareFlow (6 jobs total: 3 staging + 3 prod)**:
- Monthly: $0.30 ($0.10 × 3 prod jobs above free tier)
- Annual: $3.60

### Related Costs

- **Cloud Run**: Pay-per-use (depends on agent execution time)
- **Twilio Voice**: Variable (per minute of patient call)
- **Cloud Logging**: ~$0.50/GB (first 50 GB/month free)

**Total Scheduler Cost**: ~$4/year ✅

---

## �� Multi-Environment Strategy

The Terraform configuration uses `for_each` to deploy to **staging and production simultaneously**:

```terraform
locals {
  deploy_project_ids = {
    prod    = var.prod_project_id
    staging = var.staging_project_id
  }
}

resource "google_cloud_scheduler_job" "morning_rounds" {
  for_each = local.deploy_project_ids  # Creates 2 jobs

  name    = "${var.project_name}-morning-rounds"
  project = each.value
  uri     = var.pulse_agent_urls[each.key]
  # ...
}
```

**Result**: All resources are duplicated across environments with a single `terraform apply`.

---

## 🚦 Retry & Resilience

Each scheduler job has automatic retry configured:

```terraform
retry_config {
  retry_count          = 3       # Max 3 attempts
  max_retry_duration   = "0s"    # No exponential cap
  min_backoff_duration = "60s"   # Wait 1 minute between retries
  max_backoff_duration = "300s"  # Max 5 minutes backoff
}
```

**Retry Scenarios**:
- Cloud Run service is scaling (cold start)
- Temporary network issues
- Rate limiting from downstream services (Twilio, Firestore)

---

## 🌍 Future Enhancements

### 1. Multi-Hospital Support

When scaling to multiple hospitals, add hospital-specific jobs:

```terraform
variable "hospitals" {
  type = map(object({
    id   = string
    name = string
  }))
  default = {
    "hospital-a" = { id = "hosp-001", name = "General Hospital" }
    "hospital-b" = { id = "hosp-002", name = "City Medical" }
  }
}

resource "google_cloud_scheduler_job" "morning_rounds_multi" {
  for_each = var.hospitals

  name = "careflow-morning-rounds-${each.key}"
  
  http_target {
    body = base64encode(jsonencode({
      scheduleHour = 8
      hospitalId   = each.value.id
    }))
  }
}
```

### 2. Dynamic Patient-Specific Schedules

For patients with custom times (e.g., 7:00 AM, 9:30 PM):
- Store preferences in Firestore (`patients/{id}/schedulePreferences`)
- Query in agent code instead of hardcoding 3 times
- Keep main jobs as batch processors

### 3. Monitoring Dashboard

Create custom Cloud Monitoring dashboard:
- Success rate by job
- Average execution duration
- Patient call completion rate
- Twilio API errors

---

## 📚 Related Documentation

- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job)
- [OIDC Authentication for Cloud Run](https://cloud.google.com/run/docs/authenticating/service-to-service)
- [Cron Expression Syntax](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
- [CareFlow Pulse Agent Architecture](../careflow-agents/careflow-agent/README.md)
- [CareFlow Caller Agent](../careflow-agents/caller-agent/README.md)
- [A2A Protocol Specification](https://github.com/google/a2a)

---

## 🤝 Support

- **Terraform Errors**: Check `terraform.log` or run with `TF_LOG=DEBUG`
- **Scheduler Errors**: View Cloud Scheduler logs in Google Cloud Console
- **Agent Errors**: Check Cloud Run logs for `careflow-agent` service
- **Questions**: Contact DevOps team or see main project [README](../README.md)

---

**Last Updated**: January 2026  
**Terraform Version**: >= 1.0  
**Google Provider Version**: ~> 7.13.0  