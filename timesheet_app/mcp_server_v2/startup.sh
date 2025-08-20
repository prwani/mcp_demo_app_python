#!/bin/bash

# Timesheet MCP Server v2 Startup Script for Azure Web App

set -euo pipefail

echo "=== Timesheet MCP Server v2 Startup ==="

# Set environment variables
# Prefer explicit TIMESHEET_API_URL; otherwise construct from SUFFIX if provided
if [[ -z "${TIMESHEET_API_URL:-}" ]]; then
	if [[ -n "${SUFFIX:-}" ]]; then
		export TIMESHEET_API_URL="https://mcp-timesheet-api-${SUFFIX}.azurewebsites.net"
	else
		export TIMESHEET_API_URL="https://mcp-timesheet-api-1234.azurewebsites.net"
	fi
fi

# Azure Web App sets the PORT environment variable
export PORT=${PORT:-8000}

echo "Timesheet API URL: $TIMESHEET_API_URL"
echo "Port: $PORT"

# Install dependencies into writable folder and set PYTHONPATH
echo "Installing Python dependencies..."
SITE_PACKAGES_DIR="/home/site/wwwroot/.python_packages/lib/site-packages"
mkdir -p "$SITE_PACKAGES_DIR"
python3 -m pip install --no-cache-dir -r requirements.txt -t "$SITE_PACKAGES_DIR"
export PYTHONPATH="$SITE_PACKAGES_DIR:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1

echo "Starting Timesheet MCP Server v2 (FastMCP streamable-http)..."

# Start the FastMCP server
python3 server_mcp.py
