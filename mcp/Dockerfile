# ============================================================================
# CAREFLOW MCP TOOLBOX - DOCKERFILE (GENAI TOOLBOX VERSION)
# ============================================================================
# Basé sur la documentation officielle :
# https://googleapis.github.io/genai-toolbox/how-to/deploy_toolbox/

FROM us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest

WORKDIR /app

# Copy tools configuration
COPY tools.yaml .

# Cloud Run injects the PORT environment variable. 
# The toolbox binary supports the --port flag.
# We use 8080 as the default port for Cloud Run.
EXPOSE 8080

# Health check setup (the binary handles /health by default)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start the toolbox serving the local tools.yaml
# The binary is located at /app/toolbox in the official image
ENTRYPOINT ["/app/toolbox", "serve", "--tools-file", "tools.yaml", "--address", "0.0.0.0", "--port", "8080"]
