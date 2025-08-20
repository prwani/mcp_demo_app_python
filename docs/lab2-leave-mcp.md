---
title: Lab 2 — Leave MCP Server v2 (Streamable HTTP)
nav_order: 2
---

# Lab 2 — Leave MCP Server v2

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Links on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts (v2)
- Transport: HTTP (Streamable) MCP, consumed via MCP Inspector
- Tools (Leave): `apply_leave`, `get_balance`
- Prompts (Leave): `leave_application_template`, `leave_balance_inquiry`
- Resources (Leave): `leave://policies`, `leave://employee/{employee_id}/applications`
- Code: `leave_app/mcp_server_v2/server_mcp.py`

Steps
1) Deploy the v2 server with the provided script
2) Ensure `LEAVE_API_URL` points to your Leave API
3) Connect using MCP Inspector (HTTP Streamable)

What you’ll do
- Deploy only the minimal v2 server (no Docker)
- App setting `LEAVE_API_URL` points to your Leave API
- The server exposes an MCP Streamable HTTP endpoint at `/mcp`

Deploy command

<pre><code class="language-bash" data-template="SUFFIX=&lt;SUFFIX&gt; ./scripts/deploy_leave_mcp_v2.sh"></code></pre>

## Verify after deploy
- In Azure Portal > App Service > Configuration, confirm `LEAVE_API_URL` is set and correct.
- In App Service > Configuration > General settings, confirm Startup Command is `bash startup.sh`.
- In App Service > Log stream, wait for lines showing dependency install and server start (port from `PORT` env var).
- Open MCP Inspector and connect:
  - Transport: HTTP (Streamable)
  - URL: <span data-suffix-bind data-template="https://mcp-leave-mcp-v2-&lt;SUFFIX&gt;.azurewebsites.net/mcp"></span>
  - Proxy Session Token: paste the token from MCP Inspector
- In Inspector, verify:
  - Tools: `apply_leave`, `get_balance` are listed
  - Prompts: `leave_application_template`, `leave_balance_inquiry`
  - Resources: `leave://policies`, `leave://employee/{id}/applications`
- Try a tool: open `get_balance` details to see required params, then run with a test `employee_id`.

## Use MCP Inspector
- Start MCP Inspector.
- Add a server:
  - Transport: HTTP (Streamable)
  - URL: <span data-suffix-bind data-template="https://mcp-leave-mcp-v2-&lt;SUFFIX&gt;.azurewebsites.net/mcp"></span>
  - Proxy Session Token: paste the token printed by MCP Inspector
- In the connection view, verify:
  - Tools: `apply_leave`, `get_balance`
  - Prompts: `leave_application_template`, `leave_balance_inquiry`
  - Resources: `leave://policies`, `leave://employee/{id}/applications`

Validate
- Use MCP Inspector to list tools/prompts/resources and call tools.
- Note: v2 is MCP-only; REST paths aren’t exposed for curl.

Troubleshooting
- 404 when connecting? Ensure the URL ends with `/mcp`.
- Cold starts: enable Always On in the Web App.
