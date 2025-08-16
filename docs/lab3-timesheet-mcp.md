---
title: Lab 3 — Timesheet MCP Server (Option 1)
nav_order: 3
---

# Lab 3 — Timesheet MCP Server

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Examples and curl commands on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts (from README)
- Tools (Timesheet):
  - `add_timesheet_entry` — POST `/mcp/tools/add_timesheet_entry` → proxies to Timesheet API `/employees/{id}/entries`
  - `list_timesheet_entries` — GET `/mcp/tools/list_timesheet_entries?employee_id=...`
- Prompts (Timesheet):
  - `timesheet_reminder` — friendly reminder template
  - `project_time_summary` — aggregates recent entries
  - `overtime_analysis` — analyzes overtime patterns
- Resources (Timesheet):
  - Policy: `timesheet://policies/submission`
  - Codes: `timesheet://codes/projects`
  - Template: `timesheet://templates/weekly`
  - Reports/Guides: `timesheet://reports/utilization`, `timesheet://guidelines/best-practices`
- Code: `timesheet_app/mcp_server/server.py`

Steps
1) Package & deploy the Timesheet MCP server via `scripts/deploy_mcp_zip.sh`
2) Configure it to call your Timesheet API via `TIMESHEET_API_URL`
3) Validate `/mcp/health` and capability discovery

What you’ll do next (details)
- Creates `timesheet_mcp.zip` from `timesheet_app/` excluding API/web/sql
- Sets `TIMESHEET_API_URL` to your Timesheet API URL
- Sets port 8012 and startup script, deploys, restarts

Commands

<pre><code class="language-bash" data-template="# Timesheet MCP only
SUFFIX=&lt;SUFFIX&gt; DO_LEAVE=0 DO_TIMESHEET=1 DO_CHAT=0 ./scripts/deploy_mcp_zip.sh
"></code></pre>

Validate
- Health: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/health"></span>
- Tools: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list"></span>
- Prompts: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list"></span>
- Resources: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list"></span>

Try it (curl)

<pre><code class="language-bash" data-template="curl -s https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list | jq .
curl -s https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list | jq .
curl -s https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list | jq .
curl -s -X POST https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/add_timesheet_entry \
  -H 'Content-Type: application/json' \
  -d '{"employee_id":1,"entry_date":"2025-09-10","hours":8,"project":"PROJ001"}' | jq .
"></code></pre>
