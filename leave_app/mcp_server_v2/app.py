import asyncio
import os
import logging
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leave-mcp-v2-webapp")

# Pydantic models for MCP protocol
class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class Prompt(BaseModel):
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]]] = []

class Resource(BaseModel):
    uri: str
    name: str
    description: str
    mimeType: str

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class PromptRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, str]] = {}

class ResourceRequest(BaseModel):
    uri: str

# Create FastAPI app
app = FastAPI(
    title="Leave MCP Server v2",
    description="MCP-compliant leave management server with SSE transport",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration: prefer explicit LEAVE_API_URL; otherwise construct from SUFFIX
_suffix = os.getenv("SUFFIX")
_default_leave_api = (
    f"https://mcp-leave-api-{_suffix}.azurewebsites.net" if _suffix else "https://mcp-leave-api-1234.azurewebsites.net"
)
LEAVE_API_URL = os.getenv("LEAVE_API_URL", _default_leave_api)

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "Leave MCP Server v2",
        "version": "2.0.0",
        "description": "MCP-compliant leave management server",
        "transport": "SSE",
        "endpoints": {
            "sse": "/sse",
            "health": "/health",
            "tools": "/mcp/tools/list",
            "prompts": "/mcp/prompts/list",
            "resources": "/mcp/resources/list"
        },
        "mcp_version": "1.0.0",
        "leave_api_url": LEAVE_API_URL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "Leave MCP Server v2",
        "version": "2.0.0",
        "leave_api_url": LEAVE_API_URL
    }

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication"""
    logger.info("SSE connection established")
    
    async def event_stream():
        try:
            # Send initial hello message
            yield f"data: {json.dumps({'type': 'hello', 'server': 'Leave MCP Server v2', 'version': '2.0.0'})}\n\n"
            
            # Keep connection alive with periodic pings
            counter = 0
            while True:
                counter += 1
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': counter})}\n\n"
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.post("/mcp/tools/list")
async def list_tools():
    """MCP tools list endpoint"""
    tools = [
        Tool(
            name="apply_leave",
            description="Apply for leave on behalf of an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee ID"},
                    "start_date": {"type": "string", "description": "Leave start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "Leave end date (YYYY-MM-DD)"},
                    "leave_type": {"type": "string", "description": "Type of leave (vacation, sick, personal)"},
                    "reason": {"type": "string", "description": "Optional reason for leave"}
                },
                "required": ["employee_id", "start_date", "end_date", "leave_type"]
            }
        ),
        Tool(
            name="get_balance",
            description="Get leave balance for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee ID"}
                },
                "required": ["employee_id"]
            }
        )
    ]
    return {"tools": [tool.dict() for tool in tools]}

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """MCP tool call endpoint"""
    try:
        if request.name == "apply_leave":
            return await apply_leave(request.arguments)
        elif request.name == "get_balance":
            return await get_balance(request.arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Tool {request.name} not found")
    except Exception as e:
        logger.error(f"Error calling tool {request.name}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

async def apply_leave(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Apply for leave using the leave API"""
    try:
        # Validate required fields
        required_fields = ["employee_id", "start_date", "end_date", "leave_type"]
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare request data
        leave_data = {
            "employee_id": arguments["employee_id"],
            "start_date": arguments["start_date"],
            "end_date": arguments["end_date"],
            "leave_type": arguments["leave_type"],
            "reason": arguments.get("reason", "")
        }
        
        # Make API call
        response = requests.post(
            f"{LEAVE_API_URL}/leave",
            json=leave_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Leave application submitted successfully!\n\nDetails:\n{json.dumps(result, indent=2)}"
                    }
                ]
            }
        else:
            error_msg = f"Failed to apply leave. Status: {response.status_code}, Response: {response.text}"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_msg
                    }
                ],
                "isError": True
            }
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error when applying leave: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_msg
                }
            ],
            "isError": True
        }
    except Exception as e:
        error_msg = f"Error applying leave: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_msg
                }
            ],
            "isError": True
        }

async def get_balance(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get leave balance for an employee"""
    try:
        employee_id = arguments.get("employee_id")
        if not employee_id:
            raise ValueError("employee_id is required")
        
        # Make API call
        response = requests.get(
            f"{LEAVE_API_URL}/balance/{employee_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            balance_data = response.json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Leave balance for employee {employee_id}:\n\n{json.dumps(balance_data, indent=2)}"
                    }
                ]
            }
        else:
            error_msg = f"Failed to get balance. Status: {response.status_code}, Response: {response.text}"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_msg
                    }
                ],
                "isError": True
            }
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error when getting balance: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_msg
                }
            ],
            "isError": True
        }
    except Exception as e:
        error_msg = f"Error getting balance: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_msg
                }
            ],
            "isError": True
        }

@app.post("/mcp/prompts/list")
async def list_prompts():
    """MCP prompts list endpoint"""
    prompts = [
        Prompt(
            name="leave_application_template",
            description="Template for submitting a leave application",
            arguments=[
                {
                    "name": "employee_id",
                    "description": "Employee ID",
                    "required": True
                },
                {
                    "name": "leave_type",
                    "description": "Type of leave (vacation, sick, personal)",
                    "required": True
                }
            ]
        ),
        Prompt(
            name="leave_policy_guidance",
            description="Guidance on leave policies and procedures"
        )
    ]
    return {"prompts": [prompt.dict() for prompt in prompts]}

@app.post("/mcp/resources/list")
async def list_resources():
    """MCP resources list endpoint"""
    resources = [
        Resource(
            uri="leave://policies",
            name="Leave Policies",
            description="Company leave policies and procedures",
            mimeType="text/plain"
        ),
        Resource(
            uri="leave://balance/recent",
            name="Recent Leave Balance Queries",
            description="Recently queried leave balances",
            mimeType="application/json"
        )
    ]
    return {"resources": [resource.dict() for resource in resources]}

def main():
    """Main entry point for the web application"""
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting Leave MCP Server v2 web application on {host}:{port}")
    logger.info(f"Leave API URL: {LEAVE_API_URL}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
