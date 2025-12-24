# caller-agent

A base ReAct agent implemented using LangGraph with Agent2Agent (A2A) Protocol support
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.29.3`

## Project Structure

This project is organized as follows:

```
caller-agent/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── fast_api_app.py  # FastAPI Backend server
│   └── app_utils/       # App utilities and helpers
│       ├── executor/    # A2A protocol executor implementation
│       └── converters/  # Message converters for A2A protocol
├── .cloudbuild/         # CI/CD pipeline configurations for Google Cloud Build
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping and evaluation
├── tests/               # Unit, integration, and load tests
├── Makefile             # Makefile for common commands
├── GEMINI.md            # AI-assisted development guide
└── pyproject.toml       # Project dependencies and configuration
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)
- **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
- **make**: Build automation tool - [Install](https://www.gnu.org/software/make/) (pre-installed on most Unix-based systems)


## Quick Start (Local Testing)

Install required packages and launch the local development environment:

```bash
make install && make playground
```
> **📊 Observability Note:** Agent telemetry (Cloud Trace) is always enabled. Prompt-response logging is not available for LangGraph agents due to SDK limitations with streaming.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch local development environment with backend and frontend|
| `make deploy`        | Deploy agent to Cloud Run (use `IAP=true` to enable Identity-Aware Proxy, `PORT=8080` to specify container port) |
| `make local-backend` | Launch local development server with hot-reload |
| `make inspector`     | Launch A2A Protocol Inspector to test your agent implementation                             |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |
| `make setup-dev-env` | Set up development environment resources using Terraform                         |

For full command options and usage, refer to the [Makefile](Makefile).

## Using the A2A Inspector

This agent implements the [Agent2Agent (A2A) Protocol](https://a2a-protocol.org/), enabling interoperability with agents across different frameworks and languages.

The [A2A Inspector](https://github.com/a2aproject/a2a-inspector) provides the following core features:
- 🔍 View agent card and capabilities
- ✅ Validate A2A specification compliance
- 💬 Test communication with live chat interface
- 🐛 Debug with the raw message console

### Local Testing

1. Start your agent:
   ```bash
   make local-backend
   ```

2. In a separate terminal, launch the A2A Protocol Inspector:
   ```bash
   make inspector
   ```

3. Open http://localhost:5001 and connect to `http://localhost:8000`

### Remote Testing

1. Deploy your agent:
   ```bash
   make deploy
   ```

2. Launch the inspector:
   ```bash
   make inspector
   ```

3. Get an authentication token:
   ```bash
   gcloud auth print-identity-token
   ```

4. In the inspector UI at http://localhost:5001:
   - Add an HTTP header with name: `Authorization`
   - Set the value to: `Bearer <your-token-from-step-3>`
   - Connect to your deployed Cloud Run URL


## Usage

This template follows a "bring your own agent" approach - you focus on your business logic, and the template handles everything else (UI, infrastructure, deployment, monitoring).
1. **Prototype:** Build your Generative AI Agent using the intro notebooks in `notebooks/` for guidance. Use Vertex AI Evaluation to assess performance.
2. **Integrate:** Import your agent into the app by editing `app/agent.py`.
3. **Test:** Explore your agent functionality using the local playground with `make playground`. The playground automatically reloads your agent on code changes.
4. **Deploy:** Set up and initiate the CI/CD pipelines, customizing tests as necessary. Refer to the [deployment section](#deployment) for comprehensive instructions. For streamlined infrastructure deployment, simply run `uvx agent-starter-pack setup-cicd`. Check out the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently supports GitHub with both Google Cloud Build and GitHub Actions as CI/CD runners.
5. **Monitor:** Track performance and gather insights using BigQuery telemetry data, Cloud Logging, and Cloud Trace to iterate on your application.

The project includes a `GEMINI.md` file that provides context for AI tools like Gemini CLI when asking questions about your template.


## Deployment

> **Note:** For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform, you can use the [`agent-starter-pack setup-cicd` CLI command](https://googlecloudplatform.github.io/agent-starter-pack/cli/setup_cicd.html). Currently supports GitHub with both Google Cloud Build and GitHub Actions as CI/CD runners.

### Dev Environment

You can test deployment towards a Dev Environment using the following command:

```bash
gcloud config set project <your-dev-project-id>
make deploy
```


The repository includes a Terraform configuration for the setup of the Dev Google Cloud project.
See [deployment/README.md](deployment/README.md) for instructions.

### Production Deployment

The repository includes a Terraform configuration for the setup of a production Google Cloud project. Refer to [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.

## Monitoring and Observability

The application provides two levels of observability:

**1. Agent Telemetry Events (Always Enabled)**
- OpenTelemetry traces and spans exported to **Cloud Trace**
- Tracks agent execution, latency, and system metrics

**Note:** Prompt-response logging is not available for LangGraph agents due to SDK limitations with streaming responses.

See the [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability.html) for detailed instructions, example queries, and visualization options.
