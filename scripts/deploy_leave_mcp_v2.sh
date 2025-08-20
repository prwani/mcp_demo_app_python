#!/bin/bash

# Deploy Leave MCP Server v2 to Azure Web App
# Azure Web App Name: mcp-leave-mcp-v2-1234
# 
# Required Environment Variables:
#   SUFFIX - Deployment suffix (e.g., 1234)
#
# Optional Environment Variables:
#   REGION - Azure region (default: eastus)
#
# Usage:
#   SUFFIX=1234 ./scripts/deploy_leave_mcp_v2.sh

# Check for required environment variables
if [[ -z "${SUFFIX:-}" ]]; then
  echo "Error: SUFFIX is required (e.g., 1234)" >&2
  echo "Usage: SUFFIX=1234 $0" >&2
  exit 1
fi

echo "Deploying Leave MCP Server v2 to Azure Web App..."
echo "Using SUFFIX: $SUFFIX"

# Set variables using the same pattern as existing scripts
RESOURCE_GROUP="mcp-python-demo-rg-${SUFFIX}"
WEB_APP_NAME="mcp-leave-mcp-v2-${SUFFIX}"
ASP_NAME="mcp-demo-asp-${SUFFIX}"
LOCATION="${REGION:-eastus}"
SOURCE_DIR="leave_app/mcp_server_v2"

# Ensure az is logged in
if ! az account show >/dev/null 2>&1; then
  echo "Please run 'az login' first." >&2
  exit 1
fi

echo "Deploying to Resource Group: ${RESOURCE_GROUP}"
echo "Web App Name: ${WEB_APP_NAME}"

# Create ZIP file for deployment
echo "Creating deployment package..."
cd $SOURCE_DIR
zip -r ../../../leave_mcp_v2.zip . \
  -x "*.git*" "*__pycache__*" "*.pyc" \
     "Dockerfile*" "README.md" "*.md"
cd ../../..

# Check if resource group exists
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "Error: Resource group '$RESOURCE_GROUP' does not exist." >&2
  echo "Please create it first or check your SUFFIX value." >&2
  exit 1
fi

# Deploy to Azure Web App using ZIP deployment
echo "Deploying to Azure Web App: $WEB_APP_NAME"

# Create Web App if it doesn't exist
if ! az webapp show -g "$RESOURCE_GROUP" -n "$WEB_APP_NAME" >/dev/null 2>&1; then
  echo "Creating Web App: $WEB_APP_NAME"
  az webapp create \
      --resource-group $RESOURCE_GROUP \
      --plan $ASP_NAME \
      --name $WEB_APP_NAME \
      --runtime "PYTHON|3.11" \
      --startup-file "bash startup.sh"
else
  echo "Web App already exists: $WEB_APP_NAME"
fi

# Configure app settings
echo "Configuring app settings..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --settings \
    LEAVE_API_URL="https://mcp-leave-api-${SUFFIX}.azurewebsites.net" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="false" \
  ENABLE_ORYX_BUILD="false" \
    ORYX_PYTHON_VERSION="3.11" \
    PYTHON_VERSION="3.11" \
    DISABLE_COLLECTSTATIC="1" \
    WEBSITE_ENABLE_SYNC_UPDATE_SITE="1"

# Set startup command
echo "Setting startup command..."
az webapp config set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
  --startup-file "bash startup.sh"

# Deploy the ZIP file
echo "Deploying ZIP package..."
if ! az webapp deploy \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --src-path leave_mcp_v2.zip \
    --type zip; then
  echo "Primary deployment failed, trying fallback method..."
  az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --src leave_mcp_v2.zip
fi

# Restart the web app
echo "Restarting web app..."
az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME

echo "Deployment completed!"
echo "URL: https://$WEB_APP_NAME.azurewebsites.net"
echo "Health Check: https://$WEB_APP_NAME.azurewebsites.net/health"
echo "SSE Endpoint: https://$WEB_APP_NAME.azurewebsites.net/sse"

# Clean up
rm leave_mcp_v2.zip

echo "Waiting 30s for startup, then testing endpoint..."
sleep 30

# Test endpoint (prefer /health, fallback to /)
if curl -sf "https://$WEB_APP_NAME.azurewebsites.net/health" >/dev/null 2>&1; then
  echo "✓ Leave MCP Server v2 is responding (/health)"
elif curl -sf "https://$WEB_APP_NAME.azurewebsites.net/" >/dev/null 2>&1; then
  echo "✓ Leave MCP Server v2 is responding (/)"
else
  echo "✗ Leave MCP Server v2 is not responding yet (may need more time)"
fi
