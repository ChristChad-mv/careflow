# CareFlow MCP Toolbox

Model Context Protocol (MCP) toolbox for CareFlow Pulse. Provides Firestore database access via MCP protocol, enabling AI agents to query patient data, alerts, and medical records.

## 📋 What is MCP?

The **Model Context Protocol (MCP)** is an open protocol that standardizes how AI applications connect to external data sources and tools. The MCP toolbox acts as a bridge between our AI agents and Firestore database.

**Benefits:**

- 🔒 **Secure**: No direct database credentials in agent code
- 🔌 **Pluggable**: Easy to swap data sources without changing agent code
- 📊 **Structured**: Type-safe queries with validation
- 🚀 **Fast**: Direct connection to Firestore with efficient queries

## 🏗️ Architecture

```
┌─────────────────────┐
│  CareFlow Agent     │
│  (Python/LangGraph) │
└──────────┬──────────┘
           │ MCP Protocol
           │ (HTTP)
           ▼
┌─────────────────────┐
│   MCP Toolbox       │
│   (Go binary)       │
└──────────┬──────────┘
           │ Firestore API
           ▼
┌─────────────────────┐
│  Firestore Database │
│  (careflow-db)      │
└─────────────────────┘
```

## 📁 Project Structure

```
mcp/
├── tools.yaml          # MCP toolbox configuration
├── toolbox             # MCP toolbox binary (executable)
├── Dockerfile          # Container for Cloud Run deployment
├── README.md           # This file
└── deployment/         # Infrastructure as Code
    └── terraform/      # Terraform configuration
```

## 🔧 Configuration

The `tools.yaml` file defines:

1. **Data Source**: Firestore connection

   ```yaml
   sources:
     careflow-firestore:
       kind: "firestore"
       project: "careflow-478811"
       database: "careflow-db"
   ```

2. **Tools**: Available operations (queries)
   - `get_patients_for_schedule` - Get all active patients for a hospital
   - `get_patient_by_id` - Get specific patient details
   - `update_patient_status` - Update patient status
   - `get_alerts_by_severity` - Get alerts filtered by severity
   - `create_alert` - Create new alert
   - And more...

## 🚀 Quick Start (Local Development)

### Prerequisites

- Google Cloud credentials configured (Application Default Credentials)
- Access to Firestore database `careflow-db` in project `careflow-478811`

### Step 1: Download MCP Toolbox Binary

Download the latest MCP toolbox from GitHub:

```bash
# Navigate to mcp directory
cd /home/audrey/Bureau/careflow/mcp

# Download latest release (Linux x64)
curl -L https://github.com/google/genai-mcp-toolbox/releases/latest/download/toolbox-linux-amd64 -o toolbox

# Or for macOS
curl -L https://github.com/google/genai-mcp-toolbox/releases/latest/download/toolbox-darwin-amd64 -o toolbox
```

### Step 2: Make Binary Executable

```bash
chmod +x toolbox
```

### Step 3: Verify Installation

```bash
./toolbox --version
```

### Step 4: Start MCP Server

```bash
# From project root
./mcp/toolbox serve mcp/tools.yaml

# Or from mcp/ directory (Recommended for testing)
./toolbox --tools-file "tools.yaml"
```

The MCP server will start on **<http://localhost:5000>**

Expected output:

```
INFO Starting MCP toolbox server
INFO Loaded 6 tools from tools.yaml
INFO Server listening on http://localhost:5000
```

## 💻 Usage with CareFlow Agent

### 1. Start MCP Toolbox (Terminal 1)

```bash
cd /home/audrey/Bureau/careflow
./mcp/toolbox serve mcp/tools.yaml
```

### 2. Start CareFlow Pulse Agent (Terminal 2)

The agent automatically connects to MCP toolbox at startup:

```bash
cd careflow-agents/careflow-agent
source .venv/bin/activate
python app/server.py
```

The agent will discover and load all MCP tools automatically.

## 🔍 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_patients_for_schedule` | Get all active patients for a hospital | `hospitalId` (string) |
| `get_patient_by_id` | Get specific patient details | `patientId` (string) |
| `update_patient_status` | Update patient status | `patientId`, `status` |
| `get_alerts_by_severity` | Get alerts by severity level | `severity` (critical/warning/safe) |
| `create_alert` | Create new alert for patient | `patientId`, `severity`, `message` |
| `get_recent_interactions` | Get patient's recent AI interactions | `patientId`, `limit` |

## 🧪 Testing MCP Tools

Test MCP tools directly using curl:

```bash
# Get patient by ID
curl -X POST http://localhost:5000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_patient_by_id",
    "parameters": {
      "patientId": "P001"
    }
  }'
```

## 🛠️ Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9

# Or run on different port
./toolbox serve tools.yaml --port 5001
```

Then update agent configuration to use the new port.

### Authentication Error

Ensure Google Cloud credentials are configured:

```bash
# Set application default credentials
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Tool Not Found

If a tool is not discovered by the agent:

1. Check `tools.yaml` syntax
2. Restart MCP toolbox server
3. Restart agent to reload tools

### Connection Refused

If agent can't connect to MCP:

1. Verify MCP toolbox is running (`http://localhost:5000`)
2. Check firewall settings
3. Ensure correct port in agent configuration

## 📊 Monitoring

MCP toolbox provides health check endpoint:

```bash
curl http://localhost:5000/health
```

Response:

```json
{
  "status": "healthy",
  "tools_loaded": 6,
  "sources": ["careflow-firestore"]
}
```

## 🔐 Security

- MCP toolbox uses Google Cloud IAM for authentication
- No database credentials stored in configuration files
- Tools are scoped to specific collections and operations
- Rate limiting configured per tool

---

## ☁️ Cloud Deployment (Production)

For production deployment to Google Cloud Run with Terraform.

### 🏗️ Deployment Architecture

```
┌─────────────────────────────────────┐
│  GitHub Repository                  │
│  - mcp/Dockerfile                   │
│  - mcp/tools.yaml                   │
└──────────────┬──────────────────────┘
               │ Push to main
               ▼
┌─────────────────────────────────────┐
│  Cloud Build (CI/CD)                │
│  - Build Docker image               │
│  - Push to Artifact Registry        │
│  - Deploy to Cloud Run              │
└──────────────┬──────────────────────┘
               │ Deploy
               ▼
┌─────────────────────────────────────┐
│  Cloud Run (Staging/Production)     │
│  - MCP Toolbox server               │
│  - Port 5000                        │
│  - Firestore access                 │
└─────────────────────────────────────┘
```

### Prerequisites

1. **Google Cloud Projects**:
   - Production project ID
   - Staging project ID
   - CI/CD runner project ID

2. **Tools**:
   - Terraform >= 1.0.0
   - gcloud CLI configured
   - GitHub repository access

3. **Permissions**:
   - Owner/Editor on all 3 projects
   - Ability to create service accounts

### Deployment Steps

#### 1. Configure Variables

Create `deployment/terraform/terraform.tfvars`:

```hcl
# Google Cloud Projects
prod_project_id        = "careflow-prod"
staging_project_id     = "careflow-staging"
cicd_runner_project_id = "careflow-cicd"

# Deployment Configuration
project_name     = "careflow-mcp-toolbox"
region           = "us-central1"
repository_name  = "your-org/careflow"

# Firestore Configuration
firestore_database = "careflow-db"
```

#### 2. Initialize Terraform

```bash
cd /home/audrey/Bureau/careflow/mcp/deployment/terraform
terraform init
```

#### 3. Plan Deployment

```bash
terraform plan
```

This will create:

- ✅ Cloud Run services (staging + production)
- ✅ Service accounts with IAM roles
- ✅ API enablement (Cloud Run, Firestore, Logging)
- ✅ Artifact Registry setup

#### 4. Deploy Infrastructure

```bash
terraform apply
```

Confirm with `yes` when prompted.

#### 5. Verify Deployment

```bash
# Get service URLs
terraform output mcp_toolbox_urls

# Test staging
MCP_STAGING_URL=$(terraform output -json mcp_toolbox_urls | jq -r '.staging')
curl $MCP_STAGING_URL/health

# Test production
MCP_PROD_URL=$(terraform output -json mcp_toolbox_urls | jq -r '.prod')
curl $MCP_PROD_URL/health
```

### Terraform Configuration

**Key Files**:

- [deployment/terraform/main.tf](deployment/terraform/main.tf) - Cloud Run service configuration
- [deployment/terraform/variables.tf](deployment/terraform/variables.tf) - Input variables
- [deployment/terraform/iam.tf](deployment/terraform/iam.tf) - IAM permissions (Firestore access)
- [deployment/terraform/service_accounts.tf](deployment/terraform/service_accounts.tf) - Service accounts

**Service Account Roles**:

| Role | Purpose |
|------|---------|
| `roles/datastore.user` | Read/write Firestore |
| `roles/logging.logWriter` | Write logs |
| `roles/cloudtrace.agent` | Send traces |

**Cloud Run Configuration**:

- **CPU**: 1 vCPU
- **Memory**: 512 MiB
- **Min Instances**: 0 (scale to zero)
- **Max Instances**: 10
- **Timeout**: 300 seconds
- **Concurrency**: 80 requests

### Docker Container

The [Dockerfile](Dockerfile) packages the MCP toolbox binary:

```bash
# Build locally
docker build -t mcp-toolbox:local .

# Run locally with Docker
docker run -p 5000:5000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/keys/sa-key.json \
  -v /path/to/sa-key.json:/keys/sa-key.json:ro \
  mcp-toolbox:local

# Test
curl http://localhost:5000/health
```

### Updating Deployment

After modifying [tools.yaml](tools.yaml):

```bash
# Update infrastructure
cd deployment/terraform
terraform apply

# Or trigger CI/CD by pushing to main
git add tools.yaml
git commit -m "Update MCP tools configuration"
git push origin main
```

The CI/CD pipeline will automatically:

1. Build new Docker image
2. Push to Artifact Registry
3. Deploy to Cloud Run (staging → production)

### Cloud Run Logs

Monitor deployed service:

```bash
# View logs
gcloud run services logs read careflow-mcp-toolbox \
  --project=careflow-prod \
  --region=us-central1 \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail careflow-mcp-toolbox \
  --project=careflow-prod \
  --region=us-central1
```

### Cleanup

Destroy infrastructure:

```bash
cd deployment/terraform
terraform destroy
```

⚠️ **Warning**: This will delete all Cloud Run services and service accounts.

---

## 📚 Additional Resources

- [MCP Protocol Specification](https://github.com/modelcontextprotocol)
- [Google GenAI MCP Toolbox](https://github.com/google/genai-mcp-toolbox)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

## 🆘 Need Help?

### Local Startup Issues

If MCP toolbox fails to start locally:

1. ✅ Check `tools.yaml` is valid YAML
2. ✅ Verify Google Cloud credentials
3. ✅ Confirm Firestore database exists
4. ✅ Check network connectivity to GCP
5. ✅ Review logs for specific error messages

### Deployment Issues

**Error: Service account not found**

```bash
# Ensure APIs are enabled
gcloud services enable iam.googleapis.com --project=<PROJECT_ID>
terraform apply
```

**Error: Permission denied**

```bash
# Grant yourself necessary roles
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member=user:your-email@example.com \
  --role=roles/owner
```

**Service Not Starting**

```bash
# Check Cloud Run logs
gcloud run services logs read careflow-mcp-toolbox \
  --project=<PROJECT_ID> \
  --region=us-central1 \
  --limit=50
```

Common issues:

- Firestore database doesn't exist → Create it in GCP Console
- tools.yaml syntax error → Validate YAML syntax
- Binary download failed → Check network/proxy settings

---

**Quick Command Reference:**

```bash
# Download binary
curl -L https://github.com/google/genai-mcp-toolbox/releases/latest/download/toolbox-linux-amd64 -o toolbox

# Make executable
chmod +x toolbox

# Start server
./toolbox serve tools.yaml

# Test connection
curl http://localhost:5000/health
```
