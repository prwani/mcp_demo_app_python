import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .mcp_client import get_client
from fastapi.staticfiles import StaticFiles
import re
from .openai_client import ask_llm_with_config

app = FastAPI(title="MCP Chat Client v2")

LEAVE_MCP_URL = os.getenv("LEAVE_MCP_URL", "http://localhost:8011/mcp")
TIMESHEET_MCP_URL = os.getenv("TIMESHEET_MCP_URL", "http://localhost:8012/mcp")

class ChatRequest(BaseModel):
    server: str  # "leave" or "timesheet"
    intent: str  # tool name e.g., apply_leave, get_balance, add_timesheet_entry, get_timesheet_summary
    arguments: Dict[str, Any] | None = None

class ChatMessage(BaseModel):
    text: str
    employee_id: Optional[int] = None
    aoai: Optional[Dict[str, str]] = None  # endpoint, key, api_version, deployment

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/mcp/capabilities")
async def capabilities():
    try:
        tools_leave = await get_client("leave").list_tools()
        tools_time = await get_client("timesheet").list_tools()
        prompts_leave = await get_client("leave").list_prompts()
        prompts_time = await get_client("timesheet").list_prompts()
        resources_leave = await get_client("leave").list_resources()
        resources_time = await get_client("timesheet").list_resources()
        return {
            "tools": {"leave": tools_leave, "timesheet": tools_time},
            "prompts": {"leave": prompts_leave, "timesheet": prompts_time},
            "resources": {"leave": resources_leave, "timesheet": resources_time},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tool")
async def call_tool(req: ChatRequest):
    try:
        client = get_client(req.server)
        result = await client.call_tool(req.intent, req.arguments or {})
        return {"server": req.server, "tool": req.intent, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PromptRequest(BaseModel):
    server: str
    name: str
    arguments: Dict[str, Any] | None = None

@app.post("/mcp/prompt")
async def get_prompt(req: PromptRequest):
    try:
        client = get_client(req.server)
        result = await client.get_prompt(req.name, req.arguments)
        return {"server": req.server, "name": req.name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ResourceRequest(BaseModel):
    server: str
    uri: str

@app.post("/mcp/resource")
async def get_resource(req: ResourceRequest):
    try:
        client = get_client(req.server)
        result = await client.read_resource(req.uri)
        return {"server": req.server, "uri": req.uri, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Chat interface: intent detection and routing ---
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
HOURS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hours)")

@app.post("/chat")
async def chat(msg: ChatMessage):
    text = msg.text.strip()

    # LLM-first: ask the model to structure the intent
    llm_prompt = (
        "Extract a JSON object with: server ('leave'|'timesheet'), intent (tool name), "
        "arguments (object), and employee_id (number or null) from the message. "
        "Allowed intents: apply_leave, get_balance, add_timesheet_entry, get_timesheet_summary, get_project_hours. "
        "Dates must be YYYY-MM-DD. If multiple are present, map sensibly to start/end or entry_date.\n\n"
        f"Message: {text}\n"
        "Return ONLY valid JSON without commentary."
    )
    parsed = {}
    routing_mode = "llm"
    try:
        import json
        llm_reply = ask_llm_with_config(llm_prompt, msg.aoai)
        parsed = json.loads(llm_reply)
    except Exception:
        parsed = {}

    # Heuristic fallback if LLM not configured or reply invalid
    if not parsed or not isinstance(parsed, dict) or not parsed.get("intent"):
        routing_mode = "heuristic"
        text_l = text.lower()
        # Decide server
        server = None
        if any(k in text_l for k in ["leave", "vacation", "pto", "sick", "annual"]):
            server = "leave"
        if any(k in text_l for k in ["timesheet", "hours", "log", "project"]) and "leave" not in text_l:
            server = "timesheet"
        if server is None:
            # Fallback by keyword dominance
            leave_hits = sum(k in text_l for k in ["leave", "vacation", "pto", "sick", "annual"])
            time_hits = sum(k in text_l for k in ["timesheet", "hours", "log", "project"])
            server = "leave" if leave_hits >= time_hits else "timesheet"

        client = get_client(server)

        # Parse dates and hours
        dates = DATE_RE.findall(text)
        hours_match = HOURS_RE.search(text)
        hours_val: Optional[float] = float(hours_match.group(1)) if hours_match else None

        # Pick tool
        if server == "leave":
            if "balance" in text:
                if not msg.employee_id:
                    return {"routing_mode": routing_mode, "action": "need_employee_id", "message": "Please provide your employee_id"}
                result = await client.call_tool("get_balance", {"employee_id": msg.employee_id})
                return {"routing_mode": routing_mode, "action": "get_balance", "result": result}
            # apply leave
            if "apply" in text or "request" in text or ("leave" in text and len(dates) >= 2):
                if not msg.employee_id:
                    return {"routing_mode": routing_mode, "action": "need_employee_id", "message": "Please provide your employee_id"}
                if len(dates) < 2:
                    return {"routing_mode": routing_mode, "action": "need_dates", "message": "Please provide start and end dates (YYYY-MM-DD)"}
                leave_type = "sick" if "sick" in text else ("annual" if "annual" in text or "vacation" in text else "personal")
                args = {
                    "employee_id": int(msg.employee_id),
                    "start_date": dates[0],
                    "end_date": dates[1],
                    "leave_type": leave_type,
                }
                result = await client.call_tool("apply_leave", args)
                return {"routing_mode": routing_mode, "action": "apply_leave", "result": result}
            # default help
            return {"routing_mode": routing_mode, "action": "help", "message": "Try: 'check leave balance for employee 1' or 'apply leave from 2025-09-10 to 2025-09-12 for employee 1'"}

        # timesheet tools
        if server == "timesheet":
            if any(k in text for k in ["summary", "report"]) and len(dates) >= 2:
                if not msg.employee_id:
                    return {"routing_mode": routing_mode, "action": "need_employee_id", "message": "Please provide your employee_id"}
                args = {"employee_id": int(msg.employee_id), "start_date": dates[0], "end_date": dates[1]}
                result = await client.call_tool("get_timesheet_summary", args)
                return {"routing_mode": routing_mode, "action": "get_timesheet_summary", "result": result}
            if "project" in text and "hours" in text and len(dates) >= 2:
                # Try to find a simple project code token
                tokens = text.split()
                project = None
                for i, tok in enumerate(tokens):
                    if tok == "project" and i + 1 < len(tokens):
                        project = tokens[i + 1].strip(",.! ")
                        break
                if not project:
                    return {"routing_mode": routing_mode, "action": "need_project", "message": "Please specify a project code/name after the word 'project'"}
                args = {"project": project, "start_date": dates[0], "end_date": dates[1]}
                result = await client.call_tool("get_project_hours", args)
                return {"routing_mode": routing_mode, "action": "get_project_hours", "result": result}
            if any(k in text for k in ["add", "log"]) and hours_val is not None and dates:
                if not msg.employee_id:
                    return {"routing_mode": routing_mode, "action": "need_employee_id", "message": "Please provide your employee_id"}
                args = {"employee_id": int(msg.employee_id), "entry_date": dates[0], "hours": hours_val}
                result = await client.call_tool("add_timesheet_entry", args)
                return {"routing_mode": routing_mode, "action": "add_timesheet_entry", "result": result}
            return {"routing_mode": routing_mode, "action": "help", "message": "Try: 'log 8 hours on 2025-09-10 for employee 1' or 'timesheet summary 2025-09-01 to 2025-09-15 for employee 1'"}
    else:
        # Normalize result from LLM
        server = parsed.get("server")
        if server not in ("leave", "timesheet"):
            # Infer if missing
            text_l = text.lower()
            if any(k in text_l for k in ["leave", "vacation", "pto", "sick", "annual"]):
                server = "leave"
            elif any(k in text_l for k in ["timesheet", "hours", "log", "project"]):
                server = "timesheet"
            else:
                server = "leave"

        client = get_client(server)

        # Route by intent
        intent = parsed.get("intent")
        args = parsed.get("arguments") or {}
        if msg.employee_id and isinstance(args, dict) and "employee_id" not in args:
            args["employee_id"] = int(msg.employee_id)

        if server == "leave" and intent == "get_balance":
            if "employee_id" not in args:
                return {"routing_mode": routing_mode, "action": "need_employee_id", "message": "Please provide your employee_id"}
            result = await client.call_tool("get_balance", {"employee_id": int(args["employee_id"])})
            return {"routing_mode": routing_mode, "action": "get_balance", "result": result}

        if server == "leave" and intent == "apply_leave":
            required = ["employee_id", "start_date", "end_date", "leave_type"]
            if not all(k in args for k in required):
                return {"routing_mode": routing_mode, "action": "need_args", "missing": [k for k in required if k not in args]}
            result = await client.call_tool("apply_leave", {
                "employee_id": int(args["employee_id"]),
                "start_date": args["start_date"],
                "end_date": args["end_date"],
                "leave_type": args["leave_type"],
            })
            return {"routing_mode": routing_mode, "action": "apply_leave", "result": result}

        if server == "timesheet" and intent == "add_timesheet_entry":
            required = ["employee_id", "entry_date", "hours"]
            if not all(k in args for k in required):
                return {"routing_mode": routing_mode, "action": "need_args", "missing": [k for k in required if k not in args]}
            result = await client.call_tool("add_timesheet_entry", {
                "employee_id": int(args["employee_id"]),
                "entry_date": args["entry_date"],
                "hours": float(args["hours"]),
            })
            return {"routing_mode": routing_mode, "action": "add_timesheet_entry", "result": result}

        if server == "timesheet" and intent == "get_timesheet_summary":
            required = ["employee_id", "start_date", "end_date"]
            if not all(k in args for k in required):
                return {"routing_mode": routing_mode, "action": "need_args", "missing": [k for k in required if k not in args]}
            result = await client.call_tool("get_timesheet_summary", {
                "employee_id": int(args["employee_id"]),
                "start_date": args["start_date"],
                "end_date": args["end_date"],
            })
            return {"routing_mode": routing_mode, "action": "get_timesheet_summary", "result": result}

        if server == "timesheet" and intent == "get_project_hours":
            required = ["project", "start_date", "end_date"]
            if not all(k in args for k in required):
                return {"routing_mode": routing_mode, "action": "need_args", "missing": [k for k in required if k not in args]}
            result = await client.call_tool("get_project_hours", {
                "project": args["project"],
                "start_date": args["start_date"],
                "end_date": args["end_date"],
            })
            return {"routing_mode": routing_mode, "action": "get_project_hours", "result": result}

    return {"routing_mode": routing_mode, "action": "unrecognized", "message": "I couldn't map that to a supported action."}

# Static web UI
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
