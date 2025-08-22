#!/bin/bash

# Leave MCP Server v2 Startup Script for Azure Web App

set -euo pipefail

echo "=== Leave MCP Server v2 Startup ==="

# Set environment variables
# Prefer explicit LEAVE_API_URL. Otherwise, if SUFFIX is provided, construct URL using it.
if [[ -z "${LEAVE_API_URL:-}" ]]; then
	if [[ -n "${SUFFIX:-}" ]]; then
		export LEAVE_API_URL="https://mcp-leave-api-${SUFFIX}.azurewebsites.net"
	else
		export LEAVE_API_URL="https://mcp-leave-api-1234.azurewebsites.net"
	fi
fi

# Azure Web App sets the PORT environment variable
export PORT=${PORT:-8000}

echo "Leave API URL: $LEAVE_API_URL"
echo "Port: $PORT"

# Install dependencies into writable folder and set PYTHONPATH
echo "Installing Python dependencies..."
SITE_PACKAGES_DIR="/home/site/wwwroot/.python_packages/lib/site-packages"
mkdir -p "$SITE_PACKAGES_DIR"
python3 -m pip install --no-cache-dir -r requirements.txt -t "$SITE_PACKAGES_DIR"
export PYTHONPATH="$SITE_PACKAGES_DIR:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1

echo "Starting Leave MCP Server v2..."

# Start server
# Prefer the MCP-compliant FastMCP server which provides a streamable HTTP endpoint (/mcp),
# fall back to the FastAPI app (app.py) if server_mcp.py is unavailable.
if [[ -f "server_mcp.py" ]]; then
	echo "Launching MCP server (server_mcp.py) for protocol compliance and MCP Inspector support"
	# Ensure MCP_TRANSPORT defaults to streamable-http for web deployments
	export MCP_TRANSPORT=${MCP_TRANSPORT:-streamable-http}
	python3 server_mcp.py
elif [[ -f "app.py" ]]; then
	echo "server_mcp.py not found, launching FastAPI app (app.py) with explicit /mcp routes"
	python3 app.py
else
	echo "Error: Neither server_mcp.py nor app.py found. Cannot start server." >&2
	exit 1
fi
