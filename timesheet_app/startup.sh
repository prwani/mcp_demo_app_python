#!/bin/bash
set -e

echo "Starting Timesheet MCP Server startup script..."

# Navigate to the app directory
cd /home/site/wwwroot

# Upgrade pip and install requirements
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements_mcp.txt

# Start the application (files are now at root level)
echo "Starting Timesheet MCP Server..."
python startup_mcp.py
