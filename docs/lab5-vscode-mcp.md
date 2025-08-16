---
title: Lab 5 — Use VS Code with Leave & Timesheet MCP servers
nav_order: 5
---

# Lab 5 — Connect to Leave & Timesheet MCP servers from VS Code

This lab shows how to use a VS Code extension that supports MCP servers to connect to your Leave and Timesheet MCP servers (from Labs 2 and 3).

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">This page substitutes <code>&lt;SUFFIX&gt;</code> in examples with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

## Prerequisites
- Lab 2 and Lab 3 completed and reachable via HTTPS:
  - Leave MCP: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net"></span>
  - Timesheet MCP: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net"></span>
- VS Code installed
- An extension that supports adding custom MCP servers (examples include popular AI coding/agent extensions).

## Steps
1) Install an MCP-capable VS Code extension
   - In VS Code, open Extensions and search for an extension that supports Model Context Protocol (MCP) servers.
   - Install and reload VS Code if prompted.
2) Configure your MCP servers in the extension
   - Open the extension settings or command palette entry for MCP/Tools configuration.
   - Add a server with:
     - Name: Leave MCP (Option 1)
     - Base URL: <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net"></span>
     - Authentication: None (demo)
   - Add another server with:
     - Name: Timesheet MCP (Option 1)
     - Base URL: <span data-suffix-bind data-template="https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net"></span>
     - Authentication: None (demo)
3) Test discovery
   - Use the extension’s UI/commands to list MCP tools for each server.
   - You should see tools like `apply_leave`, `get_balance`, `add_timesheet_entry`, `list_timesheet_entries`.
4) Run a tool
   - Invoke `get_balance` with `employee_id = 1` on the Leave MCP server.
   - Invoke `add_timesheet_entry` with a small test payload on the Timesheet MCP server.

## Validate
- If discovery works, you’ll see tool lists and be able to run them from within VS Code.
- You can also hit the health and list endpoints in a browser to double-check:
  - <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/health"></span>
  - <span data-suffix-bind data-template="https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list"></span>

## Troubleshooting
- If tools don’t appear:
  - Verify the server is up by visiting `/mcp/health` and `/mcp/tools/list`.
  - Check App Service log stream for errors.
  - Some extensions cache connections; reload window and retry.
- If calls fail with 4xx/5xx:
  - Confirm Leave/Timesheet APIs from Lab 1 are healthy.
  - Ensure environment variables (e.g., LEAVE_API_URL/TIMESHEET_API_URL) are set in your MCP apps.
