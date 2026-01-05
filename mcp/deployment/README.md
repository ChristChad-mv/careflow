# MCP Toolbox Deployment

> **Note**: Full documentation including local setup and cloud deployment is available in [../README.md](../README.md).

This directory contains Terraform configuration for deploying CareFlow MCP Toolbox to Google Cloud Run.

## Quick Links

- **[Complete Documentation](../README.md)** - Local setup + Cloud deployment
- **[Terraform Variables](terraform/variables.tf)** - Configuration options
- **[Cloud Run Service](terraform/main.tf)** - Service configuration
- **[IAM Configuration](terraform/iam.tf)** - Permissions and roles

## Quick Deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

For detailed instructions, see the [Cloud Deployment section](../README.md#-cloud-deployment-production) in the main README.
