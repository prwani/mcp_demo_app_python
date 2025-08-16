---
title: Lab 2 — Leave MCP Server (Option 1)
nav_order: 2
---

# Lab 2 — Leave MCP Server

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 7859): </label>
  <input id="suffix-input" type="text" placeholder="7859" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Examples and curl commands on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts (from README)
- Tools (Leave):
  - `apply_leave` — POST `/mcp/tools/apply_leave` → proxies to Leave API `/employees/{id}/leave-requests`
  - `get_balance` — GET `/mcp/tools/get_balance?employee_id=...` → proxies to Leave API `/employees/{id}/balance`
- Prompts (Leave):
  - `leave_request_email` — email template with optional reason
  - `leave_policy_summary` — includes dynamic balance fetch
  - `leave_calendar_planning` — planning guidance
- Resources (Leave):
  - Policies: `leave://policies/annual`, `leave://policies/sick`
  - Forms: `leave://forms/application`
  - Data: `leave://calendar/holidays`, `leave://reports/team-status`
- Code: `leave_app/mcp_server/server.py`

Steps
1) Package & deploy the Leave MCP server via `scripts/deploy_mcp_zip.sh`
2) Configure it to call your Leave API via `LEAVE_API_URL`
3) Validate `/mcp/health` and capability discovery

What you’ll do next (details)
- Creates `leave_mcp.zip` from `leave_app/` excluding API/web/sql
- Sets `LEAVE_API_URL` to your Leave API URL
- Sets port 8011 and startup script, deploys, restarts

Commands

<pre><code class="language-bash" data-template="# Leave MCP only
SUFFIX=&lt;SUFFIX&gt; ONLY_LEAVE=1 ./scripts/deploy_mcp_zip.sh
"></code></pre>

Validate
- Health: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/health"></span>
- Tools: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list"></span>
- Prompts: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list"></span>
- Resources: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list"></span>

Try it (curl)

<pre><code class="language-bash" data-template="curl -s https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list | jq .
curl -s https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list | jq .
curl -s https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list | jq .
curl -s -X POST https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/apply_leave \
  -H 'Content-Type: application/json' \
  -d '{"employee_id":1,"start_date":"2025-09-10","end_date":"2025-09-12","leave_type":"annual"}' | jq .
"></code></pre>
