# Environment Setup Guide for MCP Server v2 Deployment

This guide explains the environment variables and prerequisites needed to deploy the MCP Server v2 components to Azure.

## Required Environment Variables

### SUFFIX (Required)
The deployment suffix that identifies your specific deployment instance.

**Example**: `1234`

This suffix is used to create unique resource names:
- Resource Group: `mcp-python-demo-rg-1234`
- Leave MCP v2: `mcp-leave-mcp-v2-1234`
- Timesheet MCP v2: `mcp-timesheet-mcp-v2-1234`

### How to Set Environment Variables

#### Option 1: Export for Current Session
```bash
export SUFFIX=1234
export REGION=eastus  # Optional, defaults to eastus
```

#### Option 2: Set for Single Command
```bash
SUFFIX=1234 ./scripts/deploy_leave_mcp_v2.sh
SUFFIX=1234 ./scripts/deploy_timesheet_mcp_v2.sh
```

#### Option 3: Create a Setup Script
Create a file `setup_env.sh`:
```bash
#!/bin/bash
export SUFFIX=1234
export REGION=eastus
echo "Environment variables set:"
echo "SUFFIX: $SUFFIX"
echo "REGION: $REGION"
```

Then source it:
```bash
chmod +x setup_env.sh
source setup_env.sh
```

## Prerequisites

### 1. Azure CLI Installation and Login
```bash
# Install Azure CLI (if not already installed)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Verify login
az account show
```

### 2. Required Azure Resources
The following resources must exist before deployment:

#### Resource Group
```bash
# Check if resource group exists
az group show --name "mcp-python-demo-rg-${SUFFIX}"

# Create if it doesn't exist
az group create --name "mcp-python-demo-rg-${SUFFIX}" --location "${REGION:-eastus}"
```

#### App Service Plan
```bash
# Check if App Service Plan exists
az appservice plan show --resource-group "mcp-python-demo-rg-${SUFFIX}" --name "mcp-demo-asp-${SUFFIX}"

# Create if it doesn't exist
az appservice plan create \
  --resource-group "mcp-python-demo-rg-${SUFFIX}" \
  --name "mcp-demo-asp-${SUFFIX}" \
  --location "${REGION:-eastus}" \
  --sku B1 \
  --is-linux
```

#### Backend API Services
Ensure these APIs are deployed and running:
- `mcp-leave-api-${SUFFIX}.azurewebsites.net`
- `mcp-timesheet-api-${SUFFIX}.azurewebsites.net`

### 3. Required Tools
- `zip` command (for creating deployment packages)
- `curl` command (for testing endpoints)

```bash
# Install on Ubuntu/Debian
sudo apt update
sudo apt install zip curl

# Install on RHEL/CentOS
sudo yum install zip curl
```

## Deployment Steps

### Step 1: Set Environment Variables
```bash
export SUFFIX=1234  # Replace with your suffix
```

### Step 2: Verify Prerequisites
```bash
# Check Azure login
az account show

# Check resource group exists
az group show --name "mcp-python-demo-rg-${SUFFIX}"

# Check backend APIs are running
curl https://mcp-leave-api-${SUFFIX}.azurewebsites.net/health
curl https://mcp-timesheet-api-${SUFFIX}.azurewebsites.net/health
```

### Step 3: Deploy MCP Servers v2
```bash
# Deploy Leave MCP Server v2
./scripts/deploy_leave_mcp_v2.sh

# Deploy Timesheet MCP Server v2
./scripts/deploy_timesheet_mcp_v2.sh
```

### Step 4: Verify Deployment
```bash
# Test Leave MCP Server v2
curl https://mcp-leave-mcp-v2-${SUFFIX}.azurewebsites.net/health

# Test Timesheet MCP Server v2
curl https://mcp-timesheet-mcp-v2-${SUFFIX}.azurewebsites.net/health
```

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUFFIX` | Yes | None | Deployment suffix for unique naming |
| `REGION` | No | `eastus` | Azure region for deployment |

## Common Issues and Solutions

### Issue: "SUFFIX is required"
**Solution**: Set the SUFFIX environment variable:
```bash
export SUFFIX=1234
```

### Issue: "Resource group does not exist"
**Solution**: Create the resource group first:
```bash
az group create --name "mcp-python-demo-rg-${SUFFIX}" --location "${REGION:-eastus}"
```

### Issue: "Please run 'az login' first"
**Solution**: Login to Azure CLI:
```bash
az login
```

### Issue: "App Service Plan not found"
**Solution**: Create the App Service Plan:
```bash
az appservice plan create \
  --resource-group "mcp-python-demo-rg-${SUFFIX}" \
  --name "mcp-demo-asp-${SUFFIX}" \
  --location "${REGION:-eastus}" \
  --sku B1 \
  --is-linux
```

### Issue: Backend API URLs not responding
**Solution**: Ensure the backend APIs are deployed first:
- Deploy leave API: `mcp-leave-api-${SUFFIX}`
- Deploy timesheet API: `mcp-timesheet-api-${SUFFIX}`

## Complete Setup Example

Here's a complete example for suffix `1234`:

```bash
# Set environment
export SUFFIX=1234
export REGION=eastus

# Login to Azure
az login

# Create resource group (if needed)
az group create --name "mcp-python-demo-rg-1234" --location "eastus"

# Create App Service Plan (if needed)
az appservice plan create \
  --resource-group "mcp-python-demo-rg-1234" \
  --name "mcp-demo-asp-1234" \
  --location "eastus" \
  --sku B1 \
  --is-linux

# Deploy MCP servers v2
./scripts/deploy_leave_mcp_v2.sh
./scripts/deploy_timesheet_mcp_v2.sh

# Test deployments
curl https://mcp-leave-mcp-v2-1234.azurewebsites.net/health
curl https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/health
```

## Final URLs

After successful deployment with SUFFIX=1234:

- **Leave MCP v2**: https://mcp-leave-mcp-v2-1234.azurewebsites.net
- **Timesheet MCP v2**: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net
- **MCP Inspector SSE URLs**:
  - Leave: https://mcp-leave-mcp-v2-1234.azurewebsites.net/sse
  - Timesheet: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/sse
