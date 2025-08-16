---
title: Lab 8 — Use Leave & Timesheet MCP in Microsoft 365 Copilot (Preview)
nav_order: 8
---

# Lab 8 — Access Leave & Timesheet MCP servers in Microsoft 365 Copilot

Note: This lab assumes your tenant has access to Copilot extensions that support MCP servers (preview capabilities and UX may vary by tenant/region).

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">This page substitutes <code>&lt;SUFFIX&gt;</code> in examples with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

## What you’ll do
- Register your Leave and Timesheet MCP servers with Microsoft 365 Copilot
- Make Copilot discover their Tools/Prompts/Resources automatically
- Validate by invoking a tool via Copilot

## Prerequisites
- Labs 2 and 3 completed and publicly reachable via HTTPS
  - Leave MCP: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net"></span>
  - Timesheet MCP: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net"></span>
- Microsoft 365 tenant admin permissions to manage Copilot extensions

## Steps
1) Open the Copilot admin experience (Copilot Studio or Copilot Admin portal)
   - Go to the Extensions/Plugins section for Microsoft 365 Copilot
2) Add a new MCP server (repeat for both Leave and Timesheet):
   - Name: “Leave MCP (Option 1)” or “Timesheet MCP (Option 1)”
   - Base URL: use the URL above
   - Authentication: None (for demo)
   - Save/Publish
3) Assign the extension to yourself or a target security group

## Validate in Copilot
- Open Microsoft 365 Copilot (web or M365 app)
- Try prompts:
  - “Use Leave MCP to list available tools.”
  - “Apply leave for employee 1 from 2025-09-10 to 2025-09-12 (vacation).”
  - “Use Timesheet MCP to add a timesheet entry for project ACME for 4 hours on 2025-09-03.”

## Troubleshooting
- If tools aren’t discovered:
  - Hit `/mcp/health` and `/mcp/tools/list` in a browser to verify reachability.
  - Check App Service Log stream for the MCP server.
  - Some tenants may cache extension discovery; wait a few minutes, then retry.
