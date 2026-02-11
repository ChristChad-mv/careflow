# ==============================================================================
# Installation & Setup
# ==============================================================================

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync

# ==============================================================================
# Playground Targets
# ==============================================================================

# Launch local dev playground
playground:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 💡 Try asking: What's the weather in San Francisco?                         |"
	@echo "==============================================================================="
	uv run uvicorn app.server:app --host localhost --port 8000 --reload &
	$(MAKE) inspector

# ==============================================================================
# Local Development Commands
# ==============================================================================

# Launch local development server with hot-reload
local-backend:
	uv run uvicorn app.server:app --host localhost --port 8000 --reload

# Start a direct chat session with the agent (bypasses server/Twilio)
chat:
	uv run chat_console.py

# Start a simulated patient handset (Connects to running server via WebSocket)
# This one is interactive and waits for port 8002 signals
phone:
	uv run scripts/console_phone.py

# ==============================================================================
# A2A Protocol Inspector
# ==============================================================================

# Launch A2A Protocol Inspector to test your agent implementation
inspector: setup-inspector-if-needed build-inspector-if-needed
	@echo "==============================================================================="
	@echo "| 🔍 A2A Protocol Inspector                                                  |"
	@echo "==============================================================================="
	@echo "| 🌐 Inspector UI: http://localhost:5001                                     |"
	@echo "|                                                                             |"
	@echo "| 💡 Testing Locally:                                                         |"
	@echo "|    Paste this URL into the inspector:                                      |"
	@echo "|    http://localhost:8000/a2a/app/.well-known/agent-card.json              |"
	@echo "|                                                                             |"
	@echo "| 💡 Testing Remote Deployment:                                               |"
	@echo "|    <SERVICE_URL>/a2a/app/.well-known/agent-card.json"
	@echo "|    (Get SERVICE_URL from 'make deploy' output or Cloud Console)            |"
	@echo "|                                                                             |"
	@echo "|    🔐 Auth: Expand 'Authentication & Headers', select 'Bearer Token',       |"
	@echo "|       and paste output of: gcloud auth print-identity-token                |"
	@echo "==============================================================================="
	@echo ""
	cd tools/a2a-inspector/backend && uv run app.py

# Internal: Setup inspector if not already present (runs once)
# TODO: Update to --branch v1.0.0 when a2a-inspector publishes releases
setup-inspector-if-needed:
	@if [ ! -d "tools/a2a-inspector" ]; then \
		echo "" && \
		echo "📦 First-time setup: Installing A2A Inspector..." && \
		echo "" && \
		mkdir -p tools && \
		git clone --quiet https://github.com/a2aproject/a2a-inspector.git tools/a2a-inspector && \
		(cd tools/a2a-inspector && git -c advice.detachedHead=false checkout --quiet 893e4062f6fbd85a8369228ce862ebbf4a025694) && \
		echo "📥 Installing Python dependencies..." && \
		(cd tools/a2a-inspector && uv sync --quiet) && \
		echo "📥 Installing Node.js dependencies..." && \
		(cd tools/a2a-inspector/frontend && npm install --silent) && \
		echo "🔨 Building frontend..." && \
		(cd tools/a2a-inspector/frontend && npm run build --silent) && \
		echo "" && \
		echo "✅ A2A Inspector setup complete!" && \
		echo ""; \
	fi

# Internal: Build inspector frontend if needed
build-inspector-if-needed:
	@if [ -d "tools/a2a-inspector" ] && [ ! -f "tools/a2a-inspector/frontend/public/script.js" ]; then \
		echo "🔨 Building inspector frontend..."; \
		cd tools/a2a-inspector/frontend && npm run build; \
	fi

# ==============================================================================
# Backend Deployment Targets
# ==============================================================================

# Deploy the agent remotely
# Usage: make deploy [IAP=true] [PORT=8080] - Set IAP=true to enable Identity-Aware Proxy, PORT to specify container port
deploy:
	PROJECT_ID=$$(gcloud config get-value project) && \
	PROJECT_NUMBER=$$(gcloud projects describe $$PROJECT_ID --format="value(projectNumber)") && \
	GOOGLE_API_KEY=$$(grep '^GOOGLE_API_KEY=' .env | cut -d= -f2-) && \
	TWILIO_ACCOUNT_SID=$$(grep '^TWILIO_ACCOUNT_SID=' .env | cut -d= -f2-) && \
	TWILIO_AUTH_TOKEN=$$(grep '^TWILIO_AUTH_TOKEN=' .env | cut -d= -f2-) && \
	TWILIO_PHONE_NUMBER=$$(grep '^TWILIO_PHONE_NUMBER=' .env | cut -d= -f2-) && \
	MODEL_ARMOR_TEMPLATE=$$(grep '^MODEL_ARMOR_TEMPLATE=' .env | cut -d= -f2-) && \
	CAREFLOW_AGENT_URL=$$(grep '^CAREFLOW_AGENT_URL=' .env | cut -d= -f2-) && \
	PUBLIC_URL=$$(grep '^PUBLIC_URL=' .env | cut -d= -f2-) && \
	MODEL_ARMOR_DISABLED=$$(grep '^MODEL_ARMOR_DISABLED=' .env | cut -d= -f2-) && \
	gcloud beta run deploy caller-agent \
		--source . \
		--memory "4Gi" \
		--project $$PROJECT_ID \
		--region "us-central1" \
		--allow-unauthenticated \
		--no-cpu-throttling \
		--labels "" \
		--update-build-env-vars "AGENT_VERSION=$(shell awk -F'"' '/^version = / {print $$2}' pyproject.toml || echo '0.0.0')" \
		--update-env-vars \
		"COMMIT_SHA=$(shell git rev-parse HEAD),APP_URL=https://caller-agent-76098664470.us-central1.run.app,GOOGLE_API_KEY=$$GOOGLE_API_KEY,TWILIO_ACCOUNT_SID=$$TWILIO_ACCOUNT_SID,TWILIO_AUTH_TOKEN=$$TWILIO_AUTH_TOKEN,TWILIO_PHONE_NUMBER=$$TWILIO_PHONE_NUMBER,GOOGLE_CLOUD_PROJECT=$$PROJECT_ID,MODEL_ARMOR_TEMPLATE=$$MODEL_ARMOR_TEMPLATE,MODEL_ARMOR_DISABLED=$$MODEL_ARMOR_DISABLED,CAREFLOW_AGENT_URL=$$CAREFLOW_AGENT_URL,PUBLIC_URL=$$PUBLIC_URL,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=False" \
		$(if $(IAP),--iap) \
		$(if $(PORT),--port=$(PORT))

# Alias for 'make deploy' for backward compatibility
backend: deploy

# ==============================================================================
# Infrastructure Setup
# ==============================================================================

# Set up development environment resources using Terraform
setup-dev-env:
	PROJECT_ID=$$(gcloud config get-value project) && \
	(cd deployment/terraform/dev && terraform init && terraform apply --var-file vars/env.tfvars --var dev_project_id=$$PROJECT_ID --auto-approve)

# ==============================================================================
# Testing & Code Quality
# ==============================================================================

# Run unit and integration tests
test:
	uv sync --dev
	uv run pytest tests/unit && uv run pytest tests/integration

# Run code quality checks (codespell, ruff, mypy)
lint:
	uv sync --dev --extra lint
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

# ==============================================================================
# Gemini Enterprise Integration
# ==============================================================================

# Register the deployed agent to Gemini Enterprise
# Usage: make register-gemini-enterprise (interactive - will prompt for required details)
# For non-interactive use, set env vars: ID or GEMINI_ENTERPRISE_APP_ID (full GE resource name)
# Optional env vars: GEMINI_DISPLAY_NAME, GEMINI_DESCRIPTION, AGENT_CARD_URL
register-gemini-enterprise:
	@PROJECT_ID=$$(gcloud config get-value project 2>/dev/null) && \
	PROJECT_NUMBER=$$(gcloud projects describe $$PROJECT_ID --format="value(projectNumber)" 2>/dev/null) && \
	uvx agent-starter-pack@0.29.3 register-gemini-enterprise \
		--agent-card-url="https://caller-agent-$$PROJECT_NUMBER.us-central1.run.app/a2a/app/.well-known/agent-card.json" \
		--deployment-target="cloud_run" \
		--project-number="$$PROJECT_NUMBER"