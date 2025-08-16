from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
import requests
from fastapi.staticfiles import StaticFiles
import logging

from .openai_client import ask_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_chat_client")

app = FastAPI(title="MCP Chat Client")

LEAVE_MCP_URL = os.getenv("LEAVE_MCP_URL", "http://localhost:8011")
TIMESHEET_MCP_URL = os.getenv("TIMESHEET_MCP_URL", "http://localhost:8012")


@app.get("/health")
def health():
    return {"status": "ok"}


class ChatMessage(BaseModel):
    text: str
    employee_id: int | None = None


class PromptRequest(BaseModel):
    server: str  # "leave" or "timesheet"
    prompt_name: str
    arguments: Dict[str, Any] | None = None


class ResourceRequest(BaseModel):
    server: str  # "leave" or "timesheet"
    resource_uri: str


@app.get("/mcp/discover")
def discover_mcp_capabilities():
    """Discover all available MCP capabilities from both servers"""
    capabilities = {"tools": {}, "prompts": {}, "resources": {}}
    
    # Discover Leave MCP capabilities
    try:
        tools_resp = requests.get(f"{LEAVE_MCP_URL}/mcp/tools/list", timeout=5)
        if tools_resp.status_code == 200:
            capabilities["tools"]["leave"] = tools_resp.json()["tools"]
    except:
        capabilities["tools"]["leave"] = []
    
    try:
        prompts_resp = requests.get(f"{LEAVE_MCP_URL}/mcp/prompts/list", timeout=5)
        if prompts_resp.status_code == 200:
            capabilities["prompts"]["leave"] = prompts_resp.json()["prompts"]
    except:
        capabilities["prompts"]["leave"] = []
    
    try:
        resources_resp = requests.get(f"{LEAVE_MCP_URL}/mcp/resources/list", timeout=5)
        if resources_resp.status_code == 200:
            capabilities["resources"]["leave"] = resources_resp.json()["resources"]
    except:
        capabilities["resources"]["leave"] = []
    
    # Discover Timesheet MCP capabilities
    try:
        tools_resp = requests.get(f"{TIMESHEET_MCP_URL}/mcp/tools/list", timeout=5)
        if tools_resp.status_code == 200:
            capabilities["tools"]["timesheet"] = tools_resp.json()["tools"]
    except:
        capabilities["tools"]["timesheet"] = []
    
    try:
        prompts_resp = requests.get(f"{TIMESHEET_MCP_URL}/mcp/prompts/list", timeout=5)
        if prompts_resp.status_code == 200:
            capabilities["prompts"]["timesheet"] = prompts_resp.json()["prompts"]
    except:
        capabilities["prompts"]["timesheet"] = []
    
    try:
        resources_resp = requests.get(f"{TIMESHEET_MCP_URL}/mcp/resources/list", timeout=5)
        if resources_resp.status_code == 200:
            capabilities["resources"]["timesheet"] = resources_resp.json()["resources"]
    except:
        capabilities["resources"]["timesheet"] = []
    
    return capabilities


@app.post("/mcp/prompts/get")
def get_mcp_prompt(request: PromptRequest):
    """Get a prompt from one of the MCP servers"""
    server_url = LEAVE_MCP_URL if request.server == "leave" else TIMESHEET_MCP_URL
    
    try:
        response = requests.post(
            f"{server_url}/mcp/prompts/get",
            json={"name": request.prompt_name, "arguments": request.arguments},
            timeout=10
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"MCP server error: {str(e)}")


@app.post("/mcp/resources/read")
def read_mcp_resource(request: ResourceRequest):
    """Read a resource from one of the MCP servers"""
    server_url = LEAVE_MCP_URL if request.server == "leave" else TIMESHEET_MCP_URL
    
    try:
        response = requests.post(
            f"{server_url}/mcp/resources/read",
            json={"uri": request.resource_uri},
            timeout=10
        )
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"MCP server error: {str(e)}")


@app.post("/chat")
def chat(msg: ChatMessage):
    logger.info("/chat received text='%s' employee_id=%s", msg.text, msg.employee_id)
    # Enhanced intent detection that can handle prompt and resource requests
    prompt = (
        "You are an assistant that extracts structured JSON from user messages for a workplace portal.\n"
        "Return ONLY valid JSON with keys:\n"
        "- intent: 'apply_leave', 'add_timesheet_entry', 'get_prompt', 'get_resource', 'get_balance', 'list_entries', 'smalltalk'\n"
        "- employee_id (number or null)\n"
        "- start_date (YYYY-MM-DD or null)\n"
        "- end_date (YYYY-MM-DD or null)\n"
        "- leave_type ('annual'|'sick' or null)\n"
        "- entry_date (YYYY-MM-DD or null)\n"
        "- hours (number or null)\n"
        "- server ('leave'|'timesheet' or null)\n"
        "- prompt_name (string or null)\n"
        "- resource_uri (string or null)\n"
        "- extract_args (object with relevant prompt arguments or null)\n"
        f"Message: {msg.text}\n"
    )
    parsed = {}
    try:
        reply = ask_llm(prompt)
        import json
        parsed = json.loads(reply)
    except Exception:
        parsed = {}

    # Enhanced fallback heuristics
    text = msg.text.lower()
    if not parsed:
        if "prompt" in text or "template" in text or "email" in text:
            parsed = {"intent": "get_prompt"}
        elif "policy" in text or "resource" in text or "guidelines" in text:
            parsed = {"intent": "get_resource"}
        elif "balance" in text and "leave" in text:
            parsed = {"intent": "get_balance"}
        # Recognize common verbs for retrieval (show/see/view/list) with entries/timesheet
        elif (any(k in text for k in ["list", "show", "see", "view"]) and
              ("timesheet" in text or "entries" in text or "logs" in text)):
            parsed = {"intent": "list_entries"}
        elif "leave" in text or "vacation" in text:
            parsed = {"intent": "apply_leave"}
        elif "timesheet" in text or "hours" in text or "log" in text:
            parsed = {"intent": "add_timesheet_entry"}
        else:
            parsed = {"intent": "smalltalk"}

    # Safety override: if user clearly wants to view entries, prefer list over add
    if parsed.get("intent") == "add_timesheet_entry" and (
        "entries" in text or "show" in text or "see" in text or "view" in text
    ):
        parsed["intent"] = "list_entries"

    intent = parsed.get("intent")
    logger.info("Parsed intent=%s payload_keys=%s", intent, list(parsed.keys()))
    
    # Handle new prompt requests
    if intent == "get_prompt":
        server = parsed.get("server") or ("leave" if "leave" in text else "timesheet")
        prompt_name = parsed.get("prompt_name")
        
        # Auto-detect prompt name if not specified
        if not prompt_name:
            if "email" in text or "request" in text:
                prompt_name = "leave_request_email" if server == "leave" else "timesheet_reminder"
            elif "policy" in text or "summary" in text:
                prompt_name = "leave_policy_summary" if server == "leave" else "project_time_summary"
            elif "planning" in text or "calendar" in text:
                prompt_name = "leave_calendar_planning" if server == "leave" else "overtime_analysis"
            else:
                # List available prompts
                try:
                    server_url = LEAVE_MCP_URL if server == "leave" else TIMESHEET_MCP_URL
                    prompts_resp = requests.get(f"{server_url}/mcp/prompts/list", timeout=5)
                    if prompts_resp.status_code == 200:
                        prompts = prompts_resp.json()["prompts"]
                        return {
                            "action": "list_prompts",
                            "server": server,
                            "result": prompts
                        }
                except:
                    pass
                raise HTTPException(status_code=400, detail="Please specify a prompt name")
        
        arguments = parsed.get("extract_args") or {}
        if msg.employee_id and isinstance(arguments, dict):
            arguments["employee_id"] = msg.employee_id
        
        try:
            server_url = LEAVE_MCP_URL if server == "leave" else TIMESHEET_MCP_URL
            response = requests.post(
                f"{server_url}/mcp/prompts/get",
                json={"name": prompt_name, "arguments": arguments},
                timeout=10
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return {"action": "get_prompt", "server": server, "prompt_name": prompt_name, "result": response.json()}
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"MCP server error: {str(e)}")
    
    # Handle resource requests
    if intent == "get_resource":
        server = parsed.get("server") or ("leave" if "leave" in text else "timesheet")
        resource_uri = parsed.get("resource_uri")
        
        # Auto-detect resource URI if not specified
        if not resource_uri:
            if "policy" in text and "annual" in text:
                resource_uri = "leave://policies/annual"
            elif "policy" in text and "sick" in text:
                resource_uri = "leave://policies/sick"
            elif "form" in text or "application" in text:
                resource_uri = "leave://forms/application"
            elif "holiday" in text or "calendar" in text:
                resource_uri = "leave://calendar/holidays"
            elif "team" in text and "status" in text:
                resource_uri = "leave://reports/team-status"
            elif "submission" in text and "timesheet" in text:
                resource_uri = "timesheet://policies/submission"
            elif "project" in text and "code" in text:
                resource_uri = "timesheet://codes/projects"
            elif "template" in text:
                resource_uri = "timesheet://templates/weekly"
            elif "utilization" in text:
                resource_uri = "timesheet://reports/utilization"
            elif "best" in text and "practice" in text:
                resource_uri = "timesheet://guidelines/best-practices"
            else:
                # List available resources
                try:
                    server_url = LEAVE_MCP_URL if server == "leave" else TIMESHEET_MCP_URL
                    resources_resp = requests.get(f"{server_url}/mcp/resources/list", timeout=5)
                    if resources_resp.status_code == 200:
                        resources = resources_resp.json()["resources"]
                        return {
                            "action": "list_resources",
                            "server": server,
                            "result": resources
                        }
                except:
                    pass
                raise HTTPException(status_code=400, detail="Please specify a resource URI")
        
        try:
            server_url = LEAVE_MCP_URL if server == "leave" else TIMESHEET_MCP_URL
            response = requests.post(
                f"{server_url}/mcp/resources/read",
                json={"uri": resource_uri},
                timeout=10
            )
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return {"action": "get_resource", "server": server, "resource_uri": resource_uri, "result": response.json()}
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"MCP server error: {str(e)}")
    
    # Handle get balance requests
    if intent == "get_balance":
        employee_id = parsed.get("employee_id") or msg.employee_id
        if not employee_id:
            raise HTTPException(status_code=400, detail="employee_id required")
        url = f"{LEAVE_MCP_URL}/mcp/tools/get_balance?employee_id={employee_id}"
        logger.info("Calling GET %s", url)
        r = requests.get(url, timeout=10)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"action": "get_balance", "result": r.json()}
    
    # Handle list timesheet entries requests
    if intent == "list_entries":
        employee_id = parsed.get("employee_id") or msg.employee_id
        if not employee_id:
            raise HTTPException(status_code=400, detail="employee_id required")
        url = f"{TIMESHEET_MCP_URL}/mcp/tools/list_timesheet_entries?employee_id={employee_id}"
        logger.info("Calling GET %s", url)
        r = requests.get(url, timeout=10)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"action": "list_entries", "result": r.json()}

    if intent == "apply_leave":
        employee_id = parsed.get("employee_id") or msg.employee_id
        if not employee_id:
            raise HTTPException(status_code=400, detail="employee_id required")
        start = parsed.get("start_date")
        end = parsed.get("end_date")
        ltype = parsed.get("leave_type") or ("annual" if "annual" in text else ("sick" if "sick" in text else "annual"))
        if not start or not end:
            raise HTTPException(status_code=400, detail="Missing start_date or end_date")
        post_url = f"{LEAVE_MCP_URL}/mcp/tools/apply_leave"
        logger.info("Calling POST %s", post_url)
        r = requests.post(
            post_url,
            json={
                "employee_id": int(employee_id),
                "start_date": start,
                "end_date": end,
                "leave_type": ltype,
            },
            timeout=10,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"action": "apply_leave", "result": r.json()}

    if intent == "add_timesheet_entry":
        employee_id = parsed.get("employee_id") or msg.employee_id
        if not employee_id:
            raise HTTPException(status_code=400, detail="employee_id required")
        entry_date = parsed.get("entry_date")
        hours = parsed.get("hours")
        if not entry_date or hours is None:
            # very simple fallback parse
            try:
                parts = text.split()
                hours_idx = parts.index("hours")
                hours = int(parts[hours_idx - 1])
                on_idx = parts.index("on")
                entry_date = parts[on_idx + 1]
            except Exception:
                raise HTTPException(status_code=400, detail="Missing entry_date or hours")
        post_url = f"{TIMESHEET_MCP_URL}/mcp/tools/add_timesheet_entry"
        logger.info("Calling POST %s", post_url)
        r = requests.post(
            post_url,
            json={
                "employee_id": int(employee_id),
                "entry_date": entry_date,
                "hours": int(hours),
            },
            timeout=10,
        )
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return {"action": "add_timesheet_entry", "result": r.json()}

    # smalltalk
    reply = ask_llm(msg.text)
    return {"action": "llm", "result": reply}

# Serve simple web UI
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
