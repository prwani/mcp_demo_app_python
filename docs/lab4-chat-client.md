---
title: Lab 4 — MCP Chat Client (Option 1)
nav_order: 4
---

# Lab 4 — MCP Chat Client

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">Examples and curl commands on this page substitute <code>&lt;SUFFIX&gt;</code> with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

Concepts
- Discovery: client queries `/mcp/tools/list`, `/mcp/prompts/list`, `/mcp/resources/list` on both servers
- Orchestration: `/chat` endpoint parses intent and invokes MCP tools/resources
- LLM assist: optional Azure OpenAI improves intent parsing
- Code: `chat_client/api/main.py`

Steps
1) Package & deploy the Chat Client via `scripts/deploy_mcp_zip.sh`
2) Wire it to Leave/Timesheet MCP URLs via app settings
3) Test flows from the web UI

What you’ll do next (details)
- The script sets `LEAVE_MCP_URL`, `TIMESHEET_MCP_URL`, and `WEBSITES_PORT=8000`
- Optionally pass Azure OpenAI env for intent parsing: `AOAI_ENDPOINT`, `AOAI_KEY`, `AOAI_API_VERSION`, `AOAI_DEPLOYMENT`

Commands

<pre><code class="language-bash" data-template="# Chat client only (include AOAI env if available)
SUFFIX=&lt;SUFFIX&gt; DO_LEAVE=0 DO_TIMESHEET=0 DO_CHAT=1 \
AOAI_ENDPOINT=&quot;$AOAI_ENDPOINT&quot; AOAI_KEY=&quot;$AOAI_KEY&quot; AOAI_API_VERSION=&quot;$AOAI_API_VERSION&quot; AOAI_DEPLOYMENT=&quot;$AOAI_DEPLOYMENT&quot; \
./scripts/deploy_mcp_zip.sh
"></code></pre>

Validate
- Health: <span data-suffix-bind data-template="https://mcp-chat-client-<SUFFIX>.azurewebsites.net/health"></span>
- Web UI: <span data-suffix-bind data-template="https://mcp-chat-client-<SUFFIX>.azurewebsites.net/"></span>
- Try in chat:
  - "Apply annual leave 2025-08-20 to 2025-08-22 for employee 1"
  - "List my timesheet entries for employee 1"
  - "Generate a leave request email for Alice from 2025-09-10 to 2025-09-12"
  - "Show timesheet utilization policy"
