---
title: Lab 1 — Deploy Leave & Timesheet APIs (Option 1)
nav_order: 1
---

# Lab 1 — Azure resources + APIs

<div class="suffix-picker">
	<label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 7859): </label>
	<input id="suffix-input" type="text" placeholder="7859" style="width: 8em; margin-left: 0.5rem;" />
	<p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Examples and curl commands on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts
- Azure Web Apps (Linux) with Zip Deploy; no Docker
- SQLite persistence in /home/site/data
- Web UIs served from each API’s `web/` folder

Steps
1) Create RG/ASP/Web Apps (or let scripts create apps on first deploy)
2) Deploy Leave API via `scripts/deploy_leave_api_zip.sh`
3) Deploy Timesheet API via `scripts/deploy_timesheet_api_zip.sh`
4) Validate `/health` and open the root web UIs

Quick-start (optional)
```bash
# Login
az login

# Unique suffix and core names
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

Commands

<pre><code class="language-bash" data-template="# Login and variables
az login
export SUFFIX=&lt;SUFFIX&gt;

# (Optional) Create RG/ASP/apps upfront – see Azure_setup.md (steps 0–2 and 5)

# Deploy Leave API
SUFFIX=$SUFFIX ./scripts/deploy_leave_api_zip.sh

# Deploy Timesheet API
SUFFIX=$SUFFIX ./scripts/deploy_timesheet_api_zip.sh
"></code></pre>

Validate
- Leave API: <span data-suffix-bind data-template="https://mcp-leave-api-<SUFFIX>.azurewebsites.net/health"></span>
- Timesheet API: <span data-suffix-bind data-template="https://mcp-timesheet-api-<SUFFIX>.azurewebsites.net/health"></span>
- Web UIs at respective roots

Troubleshooting
- If health endpoints fail initially, wait 20–60s and retry
- Check App Service Logs > Log stream for errors
- Ensure SCM/Oryx build flags are disabled (scripts set these)
