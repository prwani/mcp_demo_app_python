---
title: Lab 6 — Build MCP servers with Azure API Management (from Lab 1 APIs)
nav_order: 6
---

# Lab 6 — Create MCP servers using Azure API Management (APIM)

You’ll create lightweight MCP server facades in Azure API Management that front the Leave and Timesheet APIs from Lab 1. This enables MCP-style Tools endpoints without deploying separate MCP app code.

<div class="suffix-picker">
  <label for="suffix-input"><strong>Enter your SUFFIX</strong> (e.g., 1234): </label>
  <input id="suffix-input" type="text" placeholder="1234" style="width: 8em; margin-left: 0.5rem;" />
  <p style="margin-top: 0.5rem; font-size: 0.9em; color: #555;">This page substitutes <code>&lt;SUFFIX&gt;</code> in examples with your value.</p>
</div>

<script src="./assets/suffix.js"></script>

## Design
Each APIM “MCP” API exposes minimal endpoints:
- GET `/mcp/health` → 200 JSON {"status": "ok"}
- GET `/mcp/tools/list` → JSON describing tools
- POST `/mcp/tools/<tool>` → forwards to backend API with simple mappings

We’ll configure two APIs:
- Leave-MCP (fronts Leave API at <span data-suffix-bind data-template="https://mcp-leave-api-<SUFFIX>.azurewebsites.net"></span>)
- Timesheet-MCP (fronts Timesheet API at <span data-suffix-bind data-template="https://mcp-timesheet-api-<SUFFIX>.azurewebsites.net"></span>)

## Create APIM (CLI — optional; portal steps equivalent)
```bash
# Variables
export RG="mcp-python-demo-rg-<SUFFIX>"
export APIM_NAME="mcp-apim-<SUFFIX>"
export LOCATION="eastus2"

# Create APIM (Consumption is cost-effective; use Standard/Premium if needed)
az apim create -g "$RG" -n "$APIM_NAME" --publisher-email you@example.com \
  --publisher-name "MCP Demo" --sku Consumption --location "$LOCATION"
```

## Leave-MCP API
1) Create an API with URL suffix leave-mcp
2) Add an operation GET /mcp/health with a mocked 200 JSON:
```xml
<policies>
  <inbound>
    <base />
    <return-response>
      <set-status code="200" reason="OK" />
      <set-header name="Content-Type" exists-action="override">
        <value>application/json</value>
      </set-header>
      <set-body>{"status":"ok"}</set-body>
    </return-response>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
  </policies>
```
3) Add GET /mcp/tools/list that returns Leave tools schema:
```xml
<policies>
  <inbound>
    <base />
    <return-response>
      <set-status code="200" reason="OK" />
      <set-header name="Content-Type" exists-action="override">
        <value>application/json</value>
      </set-header>
      <set-body>{
        "tools": [
          {
            "name": "apply_leave",
            "description": "Apply for leave on behalf of an employee",
            "inputSchema": {
              "type": "object",
              "properties": {
                "employee_id": {"type": "integer"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "leave_type": {"type": "string"},
                "reason": {"type": "string"}
              },
              "required": ["employee_id", "start_date", "end_date", "leave_type"]
            }
          },
          {
            "name": "get_balance",
            "description": "Get leave balance for an employee",
            "inputSchema": {
              "type": "object",
              "properties": {"employee_id": {"type": "integer"}},
              "required": ["employee_id"]
            }
          }
        ]
      }</set-body>
    </return-response>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```
4) Add POST /mcp/tools/apply_leave that forwards to Leave API:
```xml
<policies>
  <inbound>
    <base />
    <set-variable name="employeeId" value="@( (int)context.Request.Body.As<JObject>(preserveContent: true)["employee_id"])" />
    <set-backend-service base-url="https://mcp-leave-api-<SUFFIX>.azurewebsites.net" />
    <rewrite-uri template="/employees/@(context.Variables.GetValueOrDefault<int>("employeeId"))/leave-requests" />
    <set-body>@( context.Request.Body.As<JObject>(preserveContent: true).Remove("employee_id").ToString() )</set-body>
    <set-header name="Content-Type" exists-action="override">
      <value>application/json</value>
    </set-header>
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```
5) Add GET /mcp/tools/get_balance that forwards to Leave API:
```xml
<policies>
  <inbound>
    <base />
    <set-variable name="employeeId" value="@( (int)context.Request.OriginalUrl.Query.GetValueOrDefault("employee_id", 0) )" />
    <set-backend-service base-url="https://mcp-leave-api-<SUFFIX>.azurewebsites.net" />
    <rewrite-uri template="/employees/@(context.Variables.GetValueOrDefault<int>("employeeId"))/balance" />
  </inbound>
  <backend><base /></backend>
  <outbound><base /></outbound>
  <on-error><base /></on-error>
</policies>
```

## Timesheet-MCP API
Repeat the same pattern for the Timesheet API backend (<span data-suffix-bind data-template="https://mcp-timesheet-api-<SUFFIX>.azurewebsites.net"></span>):
- Tools: `add_timesheet_entry` (POST), `list_timesheet_entries` (GET)
- Forwarding examples:
  - POST /mcp/tools/add_timesheet_entry → POST /timesheet (body mapping)
  - GET /mcp/tools/list_timesheet_entries → GET /timesheet?employee_id=...&start_date=...&end_date=...

Tip: Disable subscription requirement for these APIs for easier integration/testing.

## Validate
- Call your APIM gateway URLs:
  - GET …/leave-mcp/mcp/health
  - GET …/leave-mcp/mcp/tools/list
  - POST …/leave-mcp/mcp/tools/apply_leave
- Verify 2xx responses and expected behavior via APIM trace.

## Hardening (optional)
- Add rate-limits and quotas
- Configure Entra ID or key auth if you need to secure tool calls
- Add Prompts/Resources endpoints using set-body policies for static content
