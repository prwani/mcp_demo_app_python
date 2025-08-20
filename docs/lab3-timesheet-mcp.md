---
title: Lab 3 — Timesheet MCP Server v2 (Streamable HTTP)
nav_order: 3
---

# Lab 3 — Timesheet MCP Server v2

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Links on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts (v2)
- Transport: HTTP (Streamable) MCP, consumed via MCP Inspector
- Tools (Timesheet): `add_timesheet_entry`, `get_timesheet_summary`, `get_project_hours`
- Prompts (Timesheet): `timesheet_entry_template`, `timesheet_reporting_guide`
- Resources (Timesheet): `timesheet://projects`, `timesheet://policies`, `timesheet://employee/{employee_id}/entries`
- Code: `timesheet_app/mcp_server_v2/server_mcp.py`

Steps
1) Deploy the v2 server with the provided script
2) Ensure `TIMESHEET_API_URL` points to your Timesheet API
3) Connect using MCP Inspector (HTTP Streamable)

What you’ll do
- Deploy only the minimal v2 server (no Docker)
- App setting `TIMESHEET_API_URL` points to your Timesheet API
- The server exposes an MCP Streamable HTTP endpoint at `/mcp`

Deploy command

<pre><code class="language-bash" data-template="SUFFIX=&lt;SUFFIX&gt; ./scripts/deploy_timesheet_mcp_v2.sh"></code></pre>

## Use MCP Inspector
- Start MCP Inspector.
- Add a server:
  - Transport: HTTP (Streamable)
  - URL: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-v2-&lt;SUFFIX&gt;.azurewebsites.net/mcp"></span>
  - Proxy Session Token: paste the token printed by MCP Inspector
- In the connection view, verify:
  - Tools: `add_timesheet_entry`, `get_timesheet_summary`, `get_project_hours`
  - Prompts: `timesheet_entry_template`, `timesheet_reporting_guide`
  - Resources: `timesheet://projects`, `timesheet://policies`, `timesheet://employee/{id}/entries`

### Screenshots (placeholders)
- Tools list view: [Add screenshot]
- Prompts list and details: [Add screenshot]
- Resources list and read view: [Add screenshot]

Validate
- Use MCP Inspector to list tools/prompts/resources and call tools.
- Note: v2 is MCP-only; REST paths aren’t exposed for curl.

Try it
- Call `add_timesheet_entry`
- Call `get_timesheet_summary`
- Call `get_project_hours`

Troubleshooting
- 404 when connecting? Ensure the URL ends with `/mcp`.
- Cold starts: enable Always On in the Web App.

## Verify after deploy
- In Azure Portal > App Service > Configuration, confirm `TIMESHEET_API_URL` is set and correct.
- In App Service > Configuration > General settings, confirm Startup Command is `bash startup.sh`.
- In App Service > Log stream, wait for lines showing dependency install and server start (port from `PORT` env var).
- Open MCP Inspector and connect:
  - Transport: HTTP (Streamable)
  - URL: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-v2-&lt;SUFFIX&gt;.azurewebsites.net/mcp"></span>
  - Proxy Session Token: paste the token from MCP Inspector
- In Inspector, verify:
  - Tools: `add_timesheet_entry`, `get_timesheet_summary`, `get_project_hours`
  - Prompts: `timesheet_entry_template`, `timesheet_reporting_guide`
  - Resources: `timesheet://projects`, `timesheet://policies`, `timesheet://employee/{id}/entries`
- Try a tool: open `add_timesheet_entry` details and run with a sample payload.
