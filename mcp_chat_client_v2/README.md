# MCP Chat Client v2

A minimal FastAPI-based client that connects to your v2 MCP servers (leave and timesheet) via Streamable HTTP using the official `mcp` Python client.

## Endpoints
- GET `/health`
- GET `/mcp/capabilities` — lists tools, prompts, and resources from both servers
- POST `/mcp/tool` — call a tool on a selected server
- POST `/mcp/prompt` — fetch a prompt from a selected server
- POST `/mcp/resource` — read a resource from a selected server

## Environment
- `LEAVE_MCP_URL` (default `http://localhost:8011/mcp`)
- `TIMESHEET_MCP_URL` (default `http://localhost:8012/mcp`)
- Optional: `MCP_PROXY_TOKEN` if your MCP servers require a Proxy Session Token header for Streamable HTTP

## Run locally
```
python -m venv .venv
. .venv/bin/activate
pip install -r mcp_chat_client_v2/requirements.txt
export LEAVE_MCP_URL=http://localhost:8011/mcp
export TIMESHEET_MCP_URL=http://localhost:8012/mcp
python mcp_chat_client_v2/startup.py
```

Then open http://localhost:8080/health
