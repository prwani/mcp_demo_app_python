# Leave MCP Server v2

This is a proper MCP (Model Context Protocol) compliant server for leave management. It implements the official MCP protocol and can be used with MCP Inspector and other MCP-compliant clients.

## Features

- **Tools**: Apply for leave, get leave balance
- **Prompts**: Leave application templates and policy guidance
- **Resources**: Leave policies and recent balance queries
- **Protocol**: Full MCP compliance with proper handshake and messaging

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Local Development (STDIO)

```bash
python server_mcp.py --transport stdio
```

This starts the server using STDIO transport for local testing with MCP Inspector.

### Web Deployment (streamable HTTP)

```bash
python server_mcp.py --transport sse --host 0.0.0.0 --port 8003
```

This starts the server with a streamable HTTP endpoint (the implementation uses an HTTP streaming transport exposed at /mcp). The README avoids naming the internal transport protocol — treat the endpoint as a generic HTTP stream that clients can consume.

### Azure Web App Deployment

This server is designed to be deployed to Azure Web App: `mcp-leave-mcp-v2-1234.azurewebsites.net`

### Deployment Steps

1. **Using the deployment script:**
   ```bash
   cd /path/to/mcp_demo_app_python
   ./scripts/deploy_leave_mcp_v2.sh
   ```

2. **Manual deployment:**
   ```bash
   # Create ZIP package
   cd leave_app/mcp_server_v2
   zip -r ../../leave_mcp_v2.zip . -x "*.git*" "*__pycache__*" "*.pyc"
   
   # Deploy using Azure CLI
   az webapp deployment source config-zip \
     --resource-group mcp-demo-rg \
   --name mcp-leave-mcp-v2-1234 \
     --src ../../leave_mcp_v2.zip
   ```

### Azure Web App Configuration

The server runs as a FastAPI application with:
- **Runtime**: Python 3.11
- **Startup Command**: `startup.sh`
- **Port**: Set by Azure Web App (usually 8000)
- **Environment Variables**:
   - `LEAVE_API_URL`: https://mcp-leave-api-1234.azurewebsites.net

### Live URLs

Once deployed, the server will be available at:
- **Main URL**: https://mcp-leave-mcp-v2-1234.azurewebsites.net
- **Health Check**: https://mcp-leave-mcp-v2-1234.azurewebsites.net/health
- **Stream Endpoint (HTTP stream)**: https://mcp-leave-mcp-v2-1234.azurewebsites.net/sse
- **MCP Tools**: https://mcp-leave-mcp-v2-1234.azurewebsites.net/mcp/tools/list

## Environment Variables

- `LEAVE_API_URL`: URL of the leave API backend (default: http://localhost:8001)
- `PORT`: Port for the streamable HTTP endpoint (default: 8003)

## MCP Inspector Connection

### For Local STDIO Server:
1. Run: `python server_mcp.py --transport stdio`
2. In MCP Inspector:
   - Transport: STDIO
   - Command: `python /path/to/server_mcp.py --transport stdio`

### For Local streamable HTTP server:
1. Run: `python server_mcp.py --transport sse --host localhost --port 8003`
2. In MCP Inspector or other MCP client tools:
   - Transport: streamable HTTP (use the HTTP stream URL)
   - URL: `http://localhost:8003/mcp`

### For Azure Web App (Live Deployment):
1. Ensure the server is deployed to Azure Web App
2. In MCP Inspector or other MCP client tools:
    - Transport: streamable HTTP
   - URL: `https://mcp-leave-mcp-v2-1234.azurewebsites.net/mcp`

Example clients

- curl (keeps connection open and prints incremental chunks):

```bash
curl -N http://localhost:8003/mcp
```

- JavaScript (browser) using EventSource to listen to the HTTP stream (works with streaming HTTP endpoints exposed as text/event-stream):

```js
const evtSource = new EventSource('http://localhost:8003/mcp');
evtSource.onmessage = (e) => {
   console.log('message', e.data);
};
evtSource.onerror = (err) => {
   console.error('stream error', err);
};
```

Note: The server exposes a streamable HTTP endpoint at `/mcp`. Consumers can use any HTTP-streaming-capable client (EventSource, fetch with ReadableStream, curl -N, etc.) to receive incremental messages without polling. The README intentionally uses the neutral term "streamable HTTP" to emphasize the generic streaming interface rather than a specific transport implementation.

## Available Tools

### apply_leave
Apply for leave on behalf of an employee.

**Parameters:**
- `employee_id` (integer): Employee ID
- `start_date` (string): Leave start date (YYYY-MM-DD)
- `end_date` (string): Leave end date (YYYY-MM-DD)
- `leave_type` (string): Type of leave (vacation, sick, personal)
- `reason` (string, optional): Reason for leave

### get_balance
Get leave balance for an employee.

**Parameters:**
- `employee_id` (integer): Employee ID

## Available Prompts

### leave_application_template
Template for submitting a leave application with guidance.

### leave_policy_guidance
Comprehensive guidance on leave policies and procedures.

## Available Resources

### leave://policies
Company leave policies and procedures document.

### leave://balance/recent
Recent leave balance queries (example data structure).

## API Integration

The server connects to your leave API backend. Ensure the API is running and accessible at the configured URL.

Expected API endpoints:
- `POST /leave` - Apply for leave
- `GET /balance/{employee_id}` - Get leave balance

## Differences from v1

- **Full MCP Protocol**: Implements proper MCP handshake and messaging
- **Transport Support**: Supports both STDIO and SSE transports
- **MCP Inspector Compatible**: Works with standard MCP tools
- **Enhanced Error Handling**: Proper MCP error responses
- **Resource Support**: Additional resources for policies and documentation
