#!/usr/bin/env bash
set -euo pipefail

# Usage: SUFFIX=1234 REGION=eastus2 ./scripts/deploy_mcp_chat_client_v2.sh

: "${SUFFIX:?Set SUFFIX like 1234}"
WEB_APP_NAME="mcp-chat-client-v2-${SUFFIX}"
RESOURCE_GROUP="mcp-python-demo-rg-${SUFFIX}"
ASP_NAME="mcp-demo-asp-${SUFFIX}"
LOCATION="${REGION:-eastus2}"
RUNTIME="PYTHON|3.11"
ZIP_FILE="/tmp/${WEB_APP_NAME}.zip"

# Resolve repo root relative to this script so it can run from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/mcp_chat_client_v2"

# Ensure Azure CLI is available
command -v az >/dev/null 2>&1 || { echo "Azure CLI (az) is required"; exit 1; }

# Ensure az is logged in
if ! az account show >/dev/null 2>&1; then
  echo "Please run 'az login' first." >&2
  exit 1
fi

# Ensure resource group exists (do not create; follow project convention)
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "Error: Resource group '$RESOURCE_GROUP' does not exist. Check SUFFIX or create it first." >&2
  exit 1
fi

# Ensure existing App Service Plan is present
if ! az appservice plan show --resource-group "$RESOURCE_GROUP" --name "$ASP_NAME" >/dev/null 2>&1; then
  echo "Error: App Service Plan '$ASP_NAME' not found in '$RESOURCE_GROUP'." >&2
  echo "Please create it or verify SUFFIX. See other scripts for the expected plan name." >&2
  exit 1
fi

# Create webapp if missing
if ! az webapp show -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" >/dev/null 2>&1; then
  az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$ASP_NAME" \
    --name "$WEB_APP_NAME" \
    --runtime "$RUNTIME" \
    --startup-file "bash startup.sh" >/dev/null
fi

# Configure app settings
az webapp config appsettings set -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=false \
  ENABLE_ORYX_BUILD=false \
  WEBSITES_PORT=8080 \
  LEAVE_MCP_URL="https://mcp-leave-mcp-v2-${SUFFIX}.azurewebsites.net/mcp" \
  TIMESHEET_MCP_URL="https://mcp-timesheet-mcp-v2-${SUFFIX}.azurewebsites.net/mcp" >/dev/null

# Set startup command
az webapp config set -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" --startup-file "bash startup.sh" >/dev/null

# Zip minimal payload
pushd "$APP_DIR" >/dev/null
zip -qr "$ZIP_FILE" . -x "**/__pycache__/**" "**/*.pyc" "**/.DS_Store" "**/.git/**"
popd >/dev/null

# Deploy
az webapp deployment source config-zip -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" --src "$ZIP_FILE" >/dev/null

# Restart
az webapp restart -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" >/dev/null

# Enable Always On
az webapp update -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" --set siteConfig.alwaysOn=true >/dev/null

echo "Deployed https://${WEB_APP_NAME}.azurewebsites.net/health"
