# MCP Server v2 Azure Deployment Guide

This guide explains how to deploy the MCP Server v2 components to Azure Web Apps.

## Azure Web Apps Created

The following Azure Web Apps will be created for the v2 MCP servers:

1. **Leave MCP Server v2**: `mcp-leave-mcp-v2-1234.azurewebsites.net`
2. **Timesheet MCP Server v2**: `mcp-timesheet-mcp-v2-1234.azurewebsites.net`

## Prerequisites

Before deploying, ensure you have the proper environment setup:

**📋 See [MCP_V2_ENVIRONMENT_SETUP.md](MCP_V2_ENVIRONMENT_SETUP.md) for detailed environment variable configuration.**

### Quick Setup
```bash
# Required environment variable
export SUFFIX=1234  # Replace with your deployment suffix

# Verify Azure CLI login
az login
az account show
```

- Azure CLI installed and configured
- Azure subscription with appropriate permissions
- Existing resource group: `mcp-python-demo-rg-${SUFFIX}`
- Existing App Service Plan: `mcp-demo-asp-${SUFFIX}`
- Backend APIs deployed and running

## Deployment Steps

### 1. Environment Setup (Required)
```bash
# Set your deployment suffix
export SUFFIX=1234  # Replace with your actual suffix

# Optional: Set region (defaults to eastus)
export REGION=eastus
```

### 2. Deploy Leave MCP Server v2

```bash
# Navigate to project root
cd /path/to/mcp_demo_app_python

# Run deployment script (SUFFIX must be set)
./scripts/deploy_leave_mcp_v2.sh
```

### 3. Deploy Timesheet MCP Server v2

```bash
# Navigate to project root
cd /path/to/mcp_demo_app_python

# Run deployment script (SUFFIX must be set)
./scripts/deploy_timesheet_mcp_v2.sh
```

## Verification

After deployment, verify the servers are running:

### Leave MCP Server v2
```bash
# Health check (replace 1234 with your SUFFIX)
curl https://mcp-leave-mcp-v2-${SUFFIX}.azurewebsites.net/health

# List tools
curl -X POST https://mcp-leave-mcp-v2-${SUFFIX}.azurewebsites.net/mcp/tools/list
```

### Timesheet MCP Server v2
```bash
# Health check (replace 1234 with your SUFFIX)
curl https://mcp-timesheet-mcp-v2-${SUFFIX}.azurewebsites.net/health

# List tools
curl -X POST https://mcp-timesheet-mcp-v2-${SUFFIX}.azurewebsites.net/mcp/tools/list
```

## MCP Inspector Configuration

Once deployed, you can connect to the servers using MCP Inspector:

### Leave MCP Server v2
- **Transport**: SSE
- **URL**: `https://mcp-leave-mcp-v2-1234.azurewebsites.net/sse`
- **Proxy Session Token**: (leave empty)

### Timesheet MCP Server v2
- **Transport**: SSE
- **URL**: `https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/sse`
- **Proxy Session Token**: (leave empty)

## Available Endpoints

Both servers expose the following endpoints:

### Standard Endpoints
- `/` - Server information
- `/health` - Health check
- `/sse` - SSE endpoint for MCP Inspector

### MCP Protocol Endpoints
- `/mcp/tools/list` - List available tools
- `/mcp/tools/call` - Execute tools
- `/mcp/prompts/list` - List available prompts
- `/mcp/prompts/get` - Get prompt content
- `/mcp/resources/list` - List available resources
- `/mcp/resources/read` - Read resource content

## Environment Configuration

The servers are configured with the following environment variables:

### Leave MCP Server v2
- `LEAVE_API_URL`: `https://mcp-leave-api-1234.azurewebsites.net`
- `PORT`: Set by Azure Web App (typically 8000)

### Timesheet MCP Server v2
- `TIMESHEET_API_URL`: `https://mcp-timesheet-api-1234.azurewebsites.net`
- `PORT`: Set by Azure Web App (typically 8000)

## Troubleshooting

### Deployment Issues
1. Check Azure CLI authentication: `az account show`
2. Verify resource group exists: `az group show -n mcp-demo-rg`
3. Check deployment logs in Azure Portal

### Runtime Issues
1. Check application logs in Azure Portal
2. Verify environment variables are set correctly
3. Test API connectivity to backend services

### MCP Inspector Connection Issues
1. Verify the server is responding: `curl https://[server-url]/health`
2. Check SSE endpoint: `curl https://[server-url]/sse`
3. Ensure transport is set to "SSE" in MCP Inspector
4. Verify URL format includes the `/sse` path

## Differences from v1

The v2 servers have these improvements over v1:

1. **True MCP Protocol Compliance**: Implements proper MCP handshake and messaging
2. **SSE Transport Support**: Compatible with MCP Inspector
3. **Enhanced Error Handling**: Proper MCP error responses
4. **Rich Resource Support**: Additional documentation and templates
5. **FastAPI Integration**: Better web server foundation for Azure deployment
6. **Comprehensive Logging**: Better monitoring and debugging capabilities

## Next Steps

After successful deployment:

1. Test the servers with MCP Inspector
2. Integrate with your MCP-enabled applications
3. Monitor performance and logs through Azure Portal
4. Set up automated deployments if needed
