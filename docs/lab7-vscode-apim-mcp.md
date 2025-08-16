---
title: Lab 7 — Use VS Code with APIM-hosted MCP servers
nav_order: 7
---

# Lab 7 — Connect to APIM-based MCP servers from VS Code

This lab shows how to use a VS Code extension that supports MCP servers to connect to the APIM-hosted MCP servers you built in Lab 6.

<div class="suffix-picker">
   <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
   <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">This page substitutes <code>&lt;SUFFIX&gt;</code> in examples with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

## Prerequisites
- Lab 6 completed; APIM exposes Leave-MCP and Timesheet-MCP endpoints
- VS Code installed
- An extension that supports adding custom MCP servers

## Steps
1) Gather your APIM URLs
   - Leave MCP via APIM: `https://<your-apim>.azure-api.net/leave-mcp`
   - Timesheet MCP via APIM: `https://<your-apim>.azure-api.net/timesheet-mcp`
2) Install and open an MCP-capable extension
3) Add the APIM-based MCP servers
   - Name: Leave MCP (APIM)
   - Base URL: your Leave APIM URL above
   - Auth: None (demo) or API key if you left subscriptions enabled
   - Repeat for Timesheet MCP (APIM)
4) Test discovery and run tools
   - List tools and invoke one (e.g., `get_balance` or `add_timesheet_entry`).

## Validate
- See tools listed and executed successfully in the extension.
- In APIM, open trace/monitoring to see incoming requests and backend responses.

## Troubleshooting
- 401/403: Ensure subscription requirement is disabled or configure the extension to send the subscription key.
- 404: Confirm your APIM API operations expose `/mcp/tools/...` and rewrite to backend paths correctly.
- Latency: APIM Consumption can cold start; try again or consider higher SKU.
