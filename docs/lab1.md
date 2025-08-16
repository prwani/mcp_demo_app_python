---
title: Lab 1 — Deploy Leave & Timesheet APIs (Option 1)
nav_order: 1
---

# Lab 1 — Azure resources + APIs

Concepts
- Azure Web Apps (Linux) with Zip Deploy; no Docker
- SQLite persistence in /home/site/data
- Web UIs served from each API’s `web/` folder

Steps
1) Create RG/ASP/Web Apps (or let scripts create apps on first deploy)
2) Deploy Leave API via `scripts/deploy_leave_api_zip.sh`
3) Deploy Timesheet API via `scripts/deploy_timesheet_api_zip.sh`
4) Validate `/health` and open the root web UIs

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
