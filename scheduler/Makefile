# CareFlow Scheduler - Makefile
# Simplifies Terraform operations for Cloud Scheduler deployment

.PHONY: help init plan apply destroy test pause resume status logs clean

TERRAFORM_DIR := terraform
REGION := us-central1
VAR_FILE := vars/prod.tfvars

help: ## Show this help message
	@echo "CareFlow Pulse - Cloud Scheduler Management"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

init: ## Initialize Terraform
	@echo "🔧 Initializing Terraform..."
	cd $(TERRAFORM_DIR) && terraform init

plan: ## Show Terraform execution plan
	@echo "📋 Planning Terraform changes..."
	cd $(TERRAFORM_DIR) && terraform plan -var-file=$(VAR_FILE)

apply: ## Deploy Cloud Scheduler jobs
	@echo "🚀 Deploying Cloud Scheduler..."
	cd $(TERRAFORM_DIR) && terraform apply -var-file=$(VAR_FILE)
	@echo ""
	@echo "✅ Deployment complete!"
	@echo ""
	@make status

destroy: ## Destroy all Cloud Scheduler resources
	@echo "⚠️  WARNING: This will delete all Cloud Scheduler jobs!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	cd $(TERRAFORM_DIR) && terraform destroy -var-file=$(VAR_FILE)

test: ## Manually trigger morning rounds (GCP Environment)
	@echo "🧪 Manually triggering morning rounds..."
	gcloud scheduler jobs run careflow-morning-rounds --location=$(REGION)
	@echo ""
	@echo "✅ Job triggered! Check logs with: make logs"

local-test: ## Trigger rounds locally on port 8080
	@echo "🧪 Triggering rounds locally on port 8080..."
	python3 run_daily_round.py --hour 8

pause: ## Pause all scheduler jobs
	@echo "⏸️  Pausing all scheduler jobs..."
	gcloud scheduler jobs pause careflow-morning-rounds --location=$(REGION) || true
	gcloud scheduler jobs pause careflow-noon-rounds --location=$(REGION) || true
	gcloud scheduler jobs pause careflow-evening-rounds --location=$(REGION) || true
	@echo "✅ All jobs paused"

resume: ## Resume all scheduler jobs
	@echo "▶️  Resuming all scheduler jobs..."
	gcloud scheduler jobs resume careflow-morning-rounds --location=$(REGION) || true
	gcloud scheduler jobs resume careflow-noon-rounds --location=$(REGION) || true
	gcloud scheduler jobs resume careflow-evening-rounds --location=$(REGION) || true
	@echo "✅ All jobs resumed"

status: ## Show status of all scheduler jobs
	@echo "📊 Scheduler Jobs Status:"
	@echo ""
	gcloud scheduler jobs list --location=$(REGION) --filter="name~careflow" --format="table(name, schedule, state, lastAttemptTime)"

logs: ## View recent scheduler execution logs
	@echo "📜 Recent Scheduler Logs (last 10):"
	@echo ""
	gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id~careflow" \
		--limit=10 \
		--format="table(timestamp, resource.labels.job_id, jsonPayload.status)" \
		--order="timestamp desc"

logs-follow: ## Follow scheduler logs in real-time
	@echo "📜 Following scheduler logs (Ctrl+C to stop)..."
	gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id~careflow" \
		--format="table(timestamp, resource.labels.job_id, jsonPayload.status)" \
		--tail

agent-logs: ## View logs from the agent triggered by scheduler
	@echo "📜 Agent Logs (triggered by scheduler):"
	@echo ""
	gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.source=cloud-scheduler" \
		--limit=20 \
		--format="table(timestamp, jsonPayload.message)" \
		--order="timestamp desc"

validate: ## Validate terraform configuration
	@echo "✔️  Validating Terraform configuration..."
	cd $(TERRAFORM_DIR) && terraform validate
	@echo "✅ Configuration valid"

fmt: ## Format terraform files
	@echo "🎨 Formatting Terraform files..."
	cd $(TERRAFORM_DIR) && terraform fmt -recursive
	@echo "✅ Files formatted"

clean: ## Clean Terraform temporary files
	@echo "🧹 Cleaning Terraform temporary files..."
	rm -rf $(TERRAFORM_DIR)/.terraform
	rm -f $(TERRAFORM_DIR)/.terraform.lock.hcl
	rm -f $(TERRAFORM_DIR)/terraform.tfstate*
	@echo "✅ Cleaned"

check-config: ## Check if vars file exists
	@if [ ! -f "$(TERRAFORM_DIR)/$(VAR_FILE)" ]; then \
		echo "❌ Error: $(VAR_FILE) not found!"; \
		echo ""; \
		echo "Please create it from the example:"; \
		echo "  cp $(TERRAFORM_DIR)/vars/env.tfvars $(TERRAFORM_DIR)/$(VAR_FILE)"; \
		echo "  edit $(TERRAFORM_DIR)/$(VAR_FILE)"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ Configuration file found"

setup: check-config init ## Initial setup (check config and initialize)
	@echo ""
	@echo "✅ Setup complete! Next steps:"
	@echo "  1. Review the plan: make plan"
	@echo "  2. Deploy: make apply"

.DEFAULT_GOAL := help
