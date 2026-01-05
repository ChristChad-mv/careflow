# ============================================================================
# CAREFLOW MCP TOOLBOX - DOCKERFILE
# ============================================================================
# Copyright (c) 2026 CareFlow Engineering Team
# Author: Christ
# Created: 2026-01-05
# License: Proprietary - All Rights Reserved
#
# Description:
#   Containerized MCP Toolbox for Cloud Run deployment with Firestore
#   integration.
# ============================================================================

FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
  ca-certificates \
  curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download latest MCP toolbox binary
RUN curl -L https://github.com/google/genai-mcp-toolbox/releases/latest/download/toolbox-linux-amd64 -o toolbox \
  && chmod +x toolbox

# Copy tools configuration
COPY tools.yaml .

# Expose MCP server port
EXPOSE 5000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Run MCP toolbox server
CMD ["./toolbox", "serve", "tools.yaml"]
