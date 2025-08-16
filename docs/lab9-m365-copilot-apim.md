---
title: Lab 9 — Use APIM-based MCP servers in Microsoft 365 Copilot (Preview)
nav_order: 9
---

# Lab 9 — Access APIM MCP servers in Microsoft 365 Copilot

You’ll connect the APIM-hosted MCP servers from Lab 6 to Microsoft 365 Copilot and validate tool execution end-to-end.

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 7859): </label>
  <input id="suffix-input" type="text" placeholder="7859" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">This page substitutes <code>&lt;SUFFIX&gt;</code> in examples with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

## Prerequisites
- Lab 6 completed; your APIM gateway exposes Leave-MCP and Timesheet-MCP APIs
- Subscription requirement disabled (or have a subscription key ready)

## Steps
1) Identify your APIM base URLs (Gateway):
   - Leave-MCP: e.g., `https://<your-apim>.azure-api.net/leave-mcp`
   - Timesheet-MCP: e.g., `https://<your-apim>.azure-api.net/timesheet-mcp`
2) In the Copilot admin experience (Extensions/Plugins): add MCP servers
   - Name: “Leave MCP (APIM)” and “Timesheet MCP (APIM)”
   - Base URL: respective APIM base URL
   - Auth: None (demo) or API key if enabled
3) Assign to yourself or target group

## Validate in Copilot
- Try:
  - “Use Leave MCP to get balance for employee 1.”
  - “Use Timesheet MCP to add 2 hours for project ACME today.”
- Watch APIM trace and analytics to confirm requests hitting your backend

## Troubleshooting
- 401/403: Disable subscription requirement or pass the key in APIM (and configure Copilot to include it if supported)
- 404 on tool routes: Ensure the APIM API path includes `/mcp/tools/...` and policies rewrite to correct backend routes
- Timeouts: Check backend App Service is warm; consider Always On
