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

---

## Lab 1 — Azure resources + deploy Leave and Timesheet APIs (Option 1)

Goal: Stand up two FastAPI apps (Leave and Timesheet) on Azure Web Apps with SQLite storage and simple web UIs.

Concepts first
- Runtime: Azure Web Apps for Linux with Zip Deploy (no Docker)
- Storage: SQLite files persist under /home/site/data
- Web UIs: each API serves a static UI from its `web/` folder (mounted at `/`)
- Health checks: `/health` endpoints to verify app readiness

What you’ll do next
1) Set variables and create the core Azure resources
2) Deploy Leave API (Zip Deploy)
3) Deploy Timesheet API (Zip Deploy)
4) Validate health and web UIs

### 1. Set environment variables and create shared resources
Use `Azure_setup.md` common steps. The commands below summarize the minimum required for Option 1.

- Define a unique SUFFIX and names
- Login, create resource group and a Linux App Service Plan
- Create the five Web Apps (runtime placeholder)

Reference: `Azure_setup.md` (steps 0–2 and 5). SQL setup is not required for Option 1.

Example quick-start (optional; you can also rely on the deploy scripts to create apps as needed):

```bash
# Login
az login

# Unique suffix
export SUFFIX=$(printf "%04d" $((RANDOM % 10000)))
export RG="mcp-python-demo-rg-$SUFFIX"
export REGION="eastus2"
export ASP_NAME="mcp-demo-asp-$SUFFIX"
export LEAVE_API_APP="mcp-leave-api-$SUFFIX"
export TIMESHEET_API_APP="mcp-timesheet-api-$SUFFIX"
export LEAVE_MCP_APP="mcp-leave-mcp-$SUFFIX"
export TIMESHEET_MCP_APP="mcp-timesheet-mcp-$SUFFIX"
export CHAT_CLIENT_APP="mcp-chat-client-$SUFFIX"

# Core resources
az group create --name "$RG" --location "$REGION"
az appservice plan create -g "$RG" -n "$ASP_NAME" --sku B1 --is-linux

# Create Web Apps (runtime placeholder)
az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$CHAT_CLIENT_APP" --runtime "PYTHON|3.10"
```

### 2. Deploy Leave API (Zip Deploy)
Concepts: FastAPI + SQLite, port 8001, startup script `startup_api.sh` invoked by App Service.

Use the provided script to package and deploy with correct app settings and startup.

- Script: `scripts/deploy_leave_api_zip.sh`
- Input: `SUFFIX` environment variable must match your resource naming
- What it does:
  - Creates `leave_api.zip` from `leave_app/` and filtered requirements
  - Sets app settings for SQLite and port 8001
  - Configures startup using `startup_api.sh`
  - Uploads the zip and restarts the app

Run:

```bash
cd /path/to/your/clone
SUFFIX=$SUFFIX ./scripts/deploy_leave_api_zip.sh
```

After the script finishes, check:
- Health: https://mcp-leave-api-<SUFFIX>.azurewebsites.net/health
- Web UI: https://mcp-leave-api-<SUFFIX>.azurewebsites.net/

### 3. Deploy Timesheet API (Zip Deploy)
Concepts: FastAPI + SQLite, port 8002, startup script `startup_api.sh`.
- Script: `scripts/deploy_timesheet_api_zip.sh`
- Input: `SUFFIX`
- What it does:
  - Creates `timesheet_api.zip` from `timesheet_app/`
  - Sets app settings for SQLite/auto and port 8002
  - Configures startup using `startup_api.sh`
  - Uploads the zip and restarts the app

Run:

```bash
cd /path/to/your/clone
SUFFIX=$SUFFIX ./scripts/deploy_timesheet_api_zip.sh
```

After the script finishes, check:
- Health: https://mcp-timesheet-api-<SUFFIX>.azurewebsites.net/health
- Web UI: https://mcp-timesheet-api-<SUFFIX>.azurewebsites.net/

Troubleshooting tips:
- If health endpoints fail initially, wait 20–60s and retry
- Check App Service Logs > Log stream for errors
- Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT` and `ENABLE_ORYX_BUILD` are disabled (the scripts set these)

---

## Lab 2 — Create and deploy the Leave MCP server (Option 1)

Goal: Publish the Leave MCP server that exposes Tools, Prompts, and Resources backed by the Leave API.

Concepts first
- Tools: `/mcp/tools/*` implements `apply_leave`, `get_balance` and proxies to Leave API (`LEAVE_API_URL`)
- Prompts: `/mcp/prompts/*` return templates; some enrich via tools (e.g., policy summary includes balances)
- Resources: `/mcp/resources/*` return policy docs, forms, calendars, team status
- Code: `leave_app/mcp_server/server.py`

What you’ll do next
1) Package and deploy the Leave MCP server
2) Configure it to call your Leave API
3) Validate MCP health and capability discovery

### Steps
- Script: `scripts/deploy_mcp_zip.sh`
- Required env: `SUFFIX` (and optionally `ONLY_LEAVE=1` to deploy just Leave MCP in this lab)
- What it does for Leave MCP:
  - Creates `leave_mcp.zip` from `leave_app/` excluding API/web/sql
  - Sets `LEAVE_API_URL` to your Leave API URL
  - Sets port 8011 and startup script
  - Deploys and restarts the app

Run (Leave MCP only):

```bash
cd /path/to/your/clone
SUFFIX=$SUFFIX ONLY_LEAVE=1 ./scripts/deploy_mcp_zip.sh
```

Validation:
- Health: https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/health
- List tools: https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list
- List prompts: https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list
- List resources: https://mcp-leave-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list

Notes:
- Tools in this server proxy to the Leave API using `LEAVE_API_URL`
- Prompts dynamically fill in arguments; some call tools (e.g., `leave_policy_summary` fetches balances)
- Resources return text or JSON describing policies, forms, holidays, and team status

---

## Lab 3 — Create and deploy the Timesheet MCP server (Option 1)

Goal: Publish the Timesheet MCP server with domain-specific tools, prompts, and resources.

Concepts first
- Tools: `/mcp/tools/*` for `add_timesheet_entry`, `list_timesheet_entries` (proxy to Timesheet API via `TIMESHEET_API_URL`)
- Prompts: reminders, project summaries, overtime analysis
- Resources: submission policy, project code directory, weekly template, utilization report, best practices
- Code: `timesheet_app/mcp_server/server.py`

What you’ll do next
1) Package and deploy the Timesheet MCP server
2) Configure it to call your Timesheet API
3) Validate MCP health and capability discovery

### Steps
- Script: `scripts/deploy_mcp_zip.sh`
- Required env: `SUFFIX` (and optionally set `DO_LEAVE=0 DO_TIMESHEET=1 DO_CHAT=0` for this lab)
- What it does for Timesheet MCP:
  - Creates `timesheet_mcp.zip` from `timesheet_app/` excluding API/web/sql
  - Sets `TIMESHEET_API_URL` to your Timesheet API URL
  - Sets port 8012 and startup script
  - Deploys and restarts the app

Run (Timesheet MCP only):

```bash
cd /path/to/your/clone
SUFFIX=$SUFFIX DO_LEAVE=0 DO_TIMESHEET=1 DO_CHAT=0 ./scripts/deploy_mcp_zip.sh
```

Validation:
- Health: https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/health
- Tools: https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/tools/list
- Prompts: https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/prompts/list
- Resources: https://mcp-timesheet-mcp-<SUFFIX>.azurewebsites.net/mcp/resources/list

---

## Lab 4 — Create and deploy the MCP Chat Client (Option 1)

Goal: Deploy a chat client that discovers MCP capabilities and calls both MCP servers. Optional Azure OpenAI improves intent extraction.

Concepts first
- Discovery: calls `/mcp/tools/list`, `/mcp/prompts/list`, `/mcp/resources/list` on both servers
- Orchestration: `/chat` parses intent and invokes tools/resources
- LLM assist: optional Azure OpenAI generates structured intents from free text
- Code: `chat_client/api/main.py`

What you’ll do next
1) Package and deploy the chat client
2) Wire it to the Leave and Timesheet MCP URLs
3) Test end-to-end flows from the web UI

### Steps
- Script: `scripts/deploy_mcp_zip.sh`
- Required env: `SUFFIX` (the script sets `LEAVE_MCP_URL`, `TIMESHEET_MCP_URL`, and port 8000)
- Optional env for Azure OpenAI intent detection:
  - `AOAI_ENDPOINT`, `AOAI_KEY`, `AOAI_API_VERSION`, `AOAI_DEPLOYMENT`

Run (Chat Client only):

```bash
cd /path/to/your/clone
# Optional: include AOAI variables for better intent extraction
SUFFIX=$SUFFIX DO_LEAVE=0 DO_TIMESHEET=0 DO_CHAT=1 \
AOAI_ENDPOINT="$AOAI_ENDPOINT" AOAI_KEY="$AOAI_KEY" AOAI_API_VERSION="$AOAI_API_VERSION" AOAI_DEPLOYMENT="$AOAI_DEPLOYMENT" \
./scripts/deploy_mcp_zip.sh
```

Validation:
- Health: https://mcp-chat-client-<SUFFIX>.azurewebsites.net/health
- Web UI: https://mcp-chat-client-<SUFFIX>.azurewebsites.net/
- Try these from the chat box:
  - "Apply annual leave 2025-08-20 to 2025-08-22 for employee 1"
  - "List my timesheet entries for employee 1"
  - "Generate a leave request email for Alice from 2025-09-10 to 2025-09-12"
  - "Show timesheet utilization policy"

---

## Appendix — Quick command snippets (optional)

Below are optional one-liners you can run yourself if not using scripts. Prefer the scripts for reliability.

- Common setup: see `Azure_setup.md`
- Option 1 basics: see `option_1_setup.md`

---

## Publish to GitHub Pages
This page lives under `docs/` so GitHub Pages can serve it from the `main` branch. After pushing:
- In your repository settings, enable Pages: Source = Deploy from a branch, Branch = `main`, Folder = `/docs`
- The workshop will be available at: `https://<your-github-username>.github.io/<repo-name>/`

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
