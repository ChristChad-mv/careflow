# ==============================================================================
# Installation & Setup
# ==============================================================================

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh; source $$HOME/.local/bin/env; }
	uv sync

# ==============================================================================
# Local Development Commands
# ==============================================================================

# Launch local development server with hot-reload
local-backend:
	uv run python -m app.server --port 8080 --reload

# Launch MCP Toolbox server locally (Requires Firestore credentials)
mcp-server:
	@echo "🚀 Starting MCP Toolbox server..."
	../../mcp/toolbox serve ../../mcp/tools.yaml

# ==============================================================================
# A2A Protocol Inspector
# ==============================================================================

# Launch A2A Protocol Inspector to test your agent implementation
inspector:
	@echo "==============================================================================="
	@echo "| 🔍 A2A Protocol Inspector                                                  |"
	@echo "==============================================================================="
	@echo "| 🌐 Inspector UI: http://localhost:5001                                     |"
	@echo "|                                                                             |"
	@echo "| 💡 Testing Locally:                                                         |"
	@echo "|    Paste this URL into the inspector:                                      |"
	@echo "|    http://localhost:8080/.well-known/agent.json                           |"
	@echo "==============================================================================="
	@echo ""
	# Assuming inspector is already setup in the workspace root or similar
	@if [ -d "../caller-agent/tools/a2a-inspector" ]; then \
		cd ../caller-agent/tools/a2a-inspector/backend && uv run app.py; \
	else \
		echo "A2A Inspector not found. Please setup in caller-agent first."; \
	fi

# ==============================================================================
# Backend Deployment Targets
# ==============================================================================

# Deploy the agent remotely
deploy:
	PROJECT_ID=$$(gcloud config get-value project) && \
	PROJECT_NUMBER=$$(gcloud projects describe $$PROJECT_ID --format="value(projectNumber)") && \
	gcloud beta run deploy careflow-agent \
		--source . \
		--memory "4Gi" \
		--project $$PROJECT_ID \
		--region "us-central1" \
		--no-allow-unauthenticated \
		--no-cpu-throttling \
		--labels "" \
		--update-build-env-vars "AGENT_VERSION=$(shell awk -F'\"' '/^version = / {print $$2}' pyproject.toml || echo '0.0.0')" \
		--update-env-vars \
		"COMMIT_SHA=$(shell git rev-parse HEAD),APP_URL=https://careflow-agent-gr2rcg7pca-uc.a.run.app"

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