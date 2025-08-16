---
title: Overview
nav_order: 0
---

# Model Context Protocol (MCP) Workshop

End-to-end hands-on to build and deploy an MCP solution on Azure using Option 1 (SQLite + Zip Deploy):
- Lab 1: Deploy Leave and Timesheet APIs + web UIs
- Lab 2: Deploy Leave MCP server
- Lab 3: Deploy Timesheet MCP server
- Lab 4: Deploy MCP chat client

You’ll first review core concepts for each lab, then run the exact commands (using the provided scripts). After completion, use the chat client UI to explore MCP Tools, Prompts, and Resources.

## Prerequisites
- Azure subscription, Azure CLI installed and logged in
- Python 3.10+
- Optional: Azure OpenAI (for enhanced intent detection in chat)

## Overview

### MCP capabilities in this repo
- Tools: actionable endpoints (leave apply, balance; timesheet add/list)
- Prompts: reusable templates (leave emails, timesheet reminders, summaries)
- Resources: content and data (policies, forms, project codes, reports)

### Architecture
- Suffix picker
  - Enter your SUFFIX once and all examples below will reflect it automatically.

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 7859): </label>
  <input id="suffix-input" type="text" placeholder="7859" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Examples and curl commands below will substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

- Leave Application
  - REST API: FastAPI + SQLAlchemy (SQLite here; Azure SQL optional)
  - MCP Server: tools, prompts, resources for leave domain
  - Web UI: static page served by the API app
- Timesheet Application
  - REST API: FastAPI (SQLite here; Azure SQL optional)
  - MCP Server: tools, prompts, resources for timesheet domain
  - Web UI: static page served by the API app
- Chat Client
  - Discovers MCP capabilities (tools/prompts/resources) across both servers
  - Calls MCP endpoints based on user intent
  - Optional Azure OpenAI to parse free text into structured intents

---

## Labs

- [Lab 1 — Deploy Leave & Timesheet APIs (Option 1)](./lab1.md)
- [Lab 2 — Leave MCP Server (Option 1)](./lab2-leave-mcp.md)
- [Lab 3 — Timesheet MCP Server (Option 1)](./lab3-timesheet-mcp.md)
- [Lab 4 — MCP Chat Client (Option 1)](./lab4-chat-client.md)
- [Lab 5 — Use VS Code with Leave & Timesheet MCP servers](./lab5-vscode-mcp.md)
- [Lab 6 — Build MCP servers with Azure API Management (from Lab 1 APIs)](./lab6-apim-mcp.md)
- [Lab 7 — Use VS Code with APIM-hosted MCP servers](./lab7-vscode-apim-mcp.md)
- [Lab 8 — Use Leave & Timesheet MCP in Microsoft 365 Copilot (Preview)](./lab8-m365-copilot.md)
- [Lab 9 — Use APIM-based MCP in Microsoft 365 Copilot (Preview)](./lab9-m365-copilot-apim.md)

---


## Appendix — Quick command snippets (optional)

Below are optional one-liners you can run yourself if not using scripts. Prefer the scripts for reliability.

- Common setup: see `Azure_setup.md`
- Option 1 basics: see `option_1_setup.md`

---

## Repo map for this workshop
- APIs: `leave_app/api`, `timesheet_app/api`
- MCP servers: `leave_app/mcp_server`, `timesheet_app/mcp_server`
- Chat client: `chat_client/api`, web UI at `chat_client/web`
- Scripts: `scripts/` (`deploy_*_zip.sh`, `deploy_mcp_zip.sh`)
- Azure setup guides: `Azure_setup.md`, `option_1_setup.md`

## Quick references

### MCP endpoints (servers)
- Tools
  - Leave: `/mcp/tools/apply_leave`, `/mcp/tools/get_balance`
  - Timesheet: `/mcp/tools/add_timesheet_entry`, `/mcp/tools/list_timesheet_entries`
- Prompts
  - Leave: `/mcp/prompts/list` and `/mcp/prompts/get`
  - Timesheet: `/mcp/prompts/list` and `/mcp/prompts/get`
- Resources
  - Leave: `/mcp/resources/list` and `/mcp/resources/read`
  - Timesheet: `/mcp/resources/list` and `/mcp/resources/read`

### Local development (optional)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn leave_app.api.main:app --port 8001 --reload
uvicorn leave_app.mcp_server.server:app --port 8011 --reload
uvicorn timesheet_app.api.main:app --port 8002 --reload
uvicorn timesheet_app.mcp_server.server:app --port 8012 --reload
uvicorn chat_client.api.main:app --port 8000 --reload
```
