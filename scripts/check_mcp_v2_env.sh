#!/bin/bash

# Environment Verification Script for MCP Server v2 Deployment
# This script checks if all required environment variables and prerequisites are met

echo "=== MCP Server v2 Deployment Environment Check ==="
echo

# Check required environment variables
echo "1. Checking Environment Variables:"
if [[ -z "${SUFFIX:-}" ]]; then
  echo "  ✗ SUFFIX is not set (REQUIRED)"
  echo "    Set with: export SUFFIX=1234"
  exit 1
else
  echo "  ✓ SUFFIX: $SUFFIX"
fi

REGION="${REGION:-eastus}"
echo "  ✓ REGION: $REGION (using default if not set)"

# Check Azure CLI
echo
echo "2. Checking Azure CLI:"
if ! command -v az >/dev/null 2>&1; then
  echo "  ✗ Azure CLI not installed"
  echo "    Install with: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
  exit 1
else
  echo "  ✓ Azure CLI is installed"
fi

# Check Azure login
if ! az account show >/dev/null 2>&1; then
  echo "  ✗ Not logged into Azure"
  echo "    Login with: az login"
  exit 1
else
  ACCOUNT_NAME=$(az account show --query name -o tsv)
  echo "  ✓ Logged into Azure: $ACCOUNT_NAME"
fi

# Check required tools
echo
echo "3. Checking Required Tools:"
for tool in zip curl; do
  if command -v $tool >/dev/null 2>&1; then
    echo "  ✓ $tool is available"
  else
    echo "  ✗ $tool is not installed"
    echo "    Install with: sudo apt install $tool"
    exit 1
  fi
done

# Check Azure resources
echo
echo "4. Checking Azure Resources:"
RESOURCE_GROUP="mcp-python-demo-rg-${SUFFIX}"
ASP_NAME="mcp-demo-asp-${SUFFIX}"

if az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "  ✓ Resource Group exists: $RESOURCE_GROUP"
else
  echo "  ✗ Resource Group missing: $RESOURCE_GROUP"
  echo "    Create with: az group create --name '$RESOURCE_GROUP' --location '$REGION'"
  exit 1
fi

if az appservice plan show --resource-group "$RESOURCE_GROUP" --name "$ASP_NAME" >/dev/null 2>&1; then
  echo "  ✓ App Service Plan exists: $ASP_NAME"
else
  echo "  ✗ App Service Plan missing: $ASP_NAME"
  echo "    Create with: az appservice plan create --resource-group '$RESOURCE_GROUP' --name '$ASP_NAME' --location '$REGION' --sku B1 --is-linux"
  exit 1
fi

# Check backend APIs
echo
echo "5. Checking Backend APIs:"
LEAVE_API_URL="https://mcp-leave-api-${SUFFIX}.azurewebsites.net"
TIMESHEET_API_URL="https://mcp-timesheet-api-${SUFFIX}.azurewebsites.net"

if curl -s "${LEAVE_API_URL}/health" >/dev/null 2>&1; then
  echo "  ✓ Leave API is responding: $LEAVE_API_URL"
else
  echo "  ⚠ Leave API not responding: $LEAVE_API_URL"
  echo "    This may cause issues during deployment"
fi

if curl -s "${TIMESHEET_API_URL}/health" >/dev/null 2>&1; then
  echo "  ✓ Timesheet API is responding: $TIMESHEET_API_URL"
else
  echo "  ⚠ Timesheet API not responding: $TIMESHEET_API_URL"
  echo "    This may cause issues during deployment"
fi

echo
echo "=== Environment Check Complete ==="
echo "✓ All prerequisites are met!"
echo
echo "You can now run the deployment scripts:"
echo "  ./scripts/deploy_leave_mcp_v2.sh"
echo "  ./scripts/deploy_timesheet_mcp_v2.sh"
echo
echo "Expected deployment URLs:"
echo "  Leave MCP v2:     https://mcp-leave-mcp-v2-${SUFFIX}.azurewebsites.net"
echo "  Timesheet MCP v2: https://mcp-timesheet-mcp-v2-${SUFFIX}.azurewebsites.net"
