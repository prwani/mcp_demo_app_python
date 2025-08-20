# Timesheet MCP Server v2

This is a proper MCP (Model Context Protocol) compliant server for timesheet management. It implements the official MCP protocol and can be used with MCP Inspector and other MCP-compliant clients.

## Features

- **Tools**: Add timesheet entries, get summaries, analyze project hours
- **Prompts**: Entry templates, reporting guides, weekly reminders
- **Resources**: Project codes, entry templates, time tracking policies
- **Protocol**: Full MCP compliance with proper handshake and messaging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Development (STDIO)

```bash
python server.py --transport stdio
```

This starts the server using STDIO transport for local testing with MCP Inspector.

### Web Deployment (SSE)

```bash
python server.py --transport sse --host 0.0.0.0 --port 8004
```

This starts the server using Server-Sent Events (SSE) transport for web deployment.

### Azure Web App Deployment

This server is designed to be deployed to Azure Web App: `mcp-timesheet-mcp-v2-1234.azurewebsites.net`

### Deployment Steps

1. **Using the deployment script:**
   ```bash
   cd /path/to/mcp_demo_app_python
   ./scripts/deploy_timesheet_mcp_v2.sh
   ```

2. **Manual deployment:**
   ```bash
   # Create ZIP package
   cd timesheet_app/mcp_server_v2
   zip -r ../../timesheet_mcp_v2.zip . -x "*.git*" "*__pycache__*" "*.pyc"
   
   # Deploy using Azure CLI
   az webapp deployment source config-zip \
     --resource-group mcp-demo-rg \
   --name mcp-timesheet-mcp-v2-1234 \
     --src ../../timesheet_mcp_v2.zip
   ```

### Azure Web App Configuration

The server runs as a FastAPI application with:
- **Runtime**: Python 3.11
- **Startup Command**: `startup.sh`
- **Port**: Set by Azure Web App (usually 8000)
- **Environment Variables**:
   - `TIMESHEET_API_URL`: https://mcp-timesheet-api-1234.azurewebsites.net

### Live URLs

Once deployed, the server will be available at:
- **Main URL**: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net
- **Health Check**: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/health
- **SSE Endpoint**: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/sse
- **MCP Tools**: https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/mcp/tools/list

## Environment Variables

- `TIMESHEET_API_URL`: URL of the timesheet API backend (default: http://localhost:8002)
- `PORT`: Port for SSE transport (default: 8004)

## MCP Inspector Connection

### For Local STDIO Server:
1. Run: `python server.py --transport stdio`
2. In MCP Inspector:
   - Transport: STDIO
   - Command: `python /path/to/server.py --transport stdio`

### For Local SSE Server:
1. Run: `python server.py --transport sse --host localhost --port 8004`
2. In MCP Inspector:
   - Transport: SSE
   - URL: `http://localhost:8004/sse`

### For Azure Web App (Live Deployment):
1. Ensure the server is deployed to Azure Web App
2. In MCP Inspector:
   - Transport: SSE
   - URL: `https://mcp-timesheet-mcp-v2-1234.azurewebsites.net/sse`

## Available Tools

### add_timesheet_entry
Add a timesheet entry for an employee.

**Parameters:**
- `employee_id` (integer): Employee ID
- `date` (string): Work date (YYYY-MM-DD)
- `hours` (number): Number of hours worked
- `project` (string): Project name or code
- `description` (string): Description of work performed

### get_timesheet_summary
Get timesheet summary for an employee for a specific period.

**Parameters:**
- `employee_id` (integer): Employee ID
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)

### get_project_hours
Get total hours worked on a specific project.

**Parameters:**
- `project` (string): Project name or code
- `start_date` (string): Start date (YYYY-MM-DD)
- `end_date` (string): End date (YYYY-MM-DD)

## Available Prompts

### timesheet_entry_template
Template for adding a timesheet entry with examples and best practices.

### timesheet_reporting_guide
Comprehensive guide for timesheet reporting and best practices.

### weekly_timesheet_reminder
Weekly reminder for timesheet submission with checklist.

## Available Resources

### timesheet://projects
JSON data containing available project codes and descriptions.

### timesheet://templates
Common timesheet entry templates for different types of work.

### timesheet://policies
Company time tracking policies and procedures.

## API Integration

The server connects to your timesheet API backend. Ensure the API is running and accessible at the configured URL.

Expected API endpoints:
- `POST /timesheet` - Add timesheet entry
- `GET /timesheet/{employee_id}/summary` - Get timesheet summary
- `GET /project/{project}/hours` - Get project hours

## Differences from v1

- **Full MCP Protocol**: Implements proper MCP handshake and messaging
- **Transport Support**: Supports both STDIO and SSE transports
- **MCP Inspector Compatible**: Works with standard MCP tools
- **Enhanced Error Handling**: Proper MCP error responses
- **Rich Resources**: Project codes, templates, and policy documentation
- **Better Prompts**: More comprehensive templates and guidance
