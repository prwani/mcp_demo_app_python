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
logger = logging.getLogger("timesheet-mcp-v2-webapp")

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
    title="Timesheet MCP Server v2",
    description="MCP-compliant timesheet management server with SSE transport",
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

# Environment configuration: prefer explicit TIMESHEET_API_URL; construct from SUFFIX otherwise
_suffix = os.getenv("SUFFIX")
_default_timesheet_api = (
    f"https://mcp-timesheet-api-{_suffix}.azurewebsites.net" if _suffix else "https://mcp-timesheet-api-1234.azurewebsites.net"
)
TIMESHEET_API_URL = os.getenv("TIMESHEET_API_URL", _default_timesheet_api)

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "Timesheet MCP Server v2",
        "version": "2.0.0",
        "description": "MCP-compliant timesheet management server",
        "transport": "SSE",
        "endpoints": {
            "sse": "/sse",
            "health": "/health",
            "tools": "/mcp/tools/list",
            "prompts": "/mcp/prompts/list",
            "resources": "/mcp/resources/list"
        },
        "mcp_version": "1.0.0",
        "timesheet_api_url": TIMESHEET_API_URL
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "Timesheet MCP Server v2",
        "version": "2.0.0",
        "timesheet_api_url": TIMESHEET_API_URL
    }

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication"""
    logger.info("SSE connection established")
    
    async def event_stream():
        try:
            # Send initial hello message
            yield f"data: {json.dumps({'type': 'hello', 'server': 'Timesheet MCP Server v2', 'version': '2.0.0'})}\n\n"
            
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
            name="add_timesheet_entry",
            description="Add a timesheet entry for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee ID"},
                    "date": {"type": "string", "description": "Work date (YYYY-MM-DD)"},
                    "hours": {"type": "number", "description": "Number of hours worked"},
                    "project": {"type": "string", "description": "Project name or code"},
                    "description": {"type": "string", "description": "Description of work performed"}
                },
                "required": ["employee_id", "date", "hours", "project", "description"]
            }
        ),
        Tool(
            name="get_timesheet_summary",
            description="Get timesheet summary for an employee for a specific period",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "integer", "description": "Employee ID"},
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                },
                "required": ["employee_id", "start_date", "end_date"]
            }
        ),
        Tool(
            name="get_project_hours",
            description="Get total hours worked on a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name or code"},
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                },
                "required": ["project", "start_date", "end_date"]
            }
        )
    ]
    return {"tools": [tool.dict() for tool in tools]}

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """MCP tool call endpoint"""
    try:
        if request.name == "add_timesheet_entry":
            return await add_timesheet_entry(request.arguments)
        elif request.name == "get_timesheet_summary":
            return await get_timesheet_summary(request.arguments)
        elif request.name == "get_project_hours":
            return await get_project_hours(request.arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Tool {request.name} not found")
    except Exception as e:
        logger.error(f"Error calling tool {request.name}: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

async def add_timesheet_entry(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Add a timesheet entry using the timesheet API"""
    try:
        # Validate required fields
        required_fields = ["employee_id", "date", "hours", "project", "description"]
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required field: {field}")
        
        # Prepare request data
        entry_data = {
            "employee_id": arguments["employee_id"],
            "date": arguments["date"],
            "hours": float(arguments["hours"]),
            "project": arguments["project"],
            "description": arguments["description"]
        }
        
        # Make API call
        response = requests.post(
            f"{TIMESHEET_API_URL}/timesheet",
            json=entry_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Timesheet entry added successfully!\n\nDetails:\n{json.dumps(result, indent=2)}"
                    }
                ]
            }
        else:
            error_msg = f"Failed to add timesheet entry. Status: {response.status_code}, Response: {response.text}"
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
        error_msg = f"Network error when adding timesheet entry: {str(e)}"
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
        error_msg = f"Error adding timesheet entry: {str(e)}"
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

async def get_timesheet_summary(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get timesheet summary for an employee"""
    try:
        # Validate required fields
        required_fields = ["employee_id", "start_date", "end_date"]
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required field: {field}")
        
        # Make API call
        params = {
            "start_date": arguments["start_date"],
            "end_date": arguments["end_date"]
        }
        response = requests.get(
            f"{TIMESHEET_API_URL}/timesheet/{arguments['employee_id']}/summary",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            summary_data = response.json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Timesheet summary for employee {arguments['employee_id']} ({arguments['start_date']} to {arguments['end_date']}):\n\n{json.dumps(summary_data, indent=2)}"
                    }
                ]
            }
        else:
            error_msg = f"Failed to get timesheet summary. Status: {response.status_code}, Response: {response.text}"
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
        error_msg = f"Network error when getting timesheet summary: {str(e)}"
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
        error_msg = f"Error getting timesheet summary: {str(e)}"
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

async def get_project_hours(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get total hours worked on a specific project"""
    try:
        # Validate required fields
        required_fields = ["project", "start_date", "end_date"]
        for field in required_fields:
            if field not in arguments:
                raise ValueError(f"Missing required field: {field}")
        
        # Make API call
        params = {
            "start_date": arguments["start_date"],
            "end_date": arguments["end_date"]
        }
        response = requests.get(
            f"{TIMESHEET_API_URL}/project/{arguments['project']}/hours",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            project_data = response.json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Project hours for {arguments['project']} ({arguments['start_date']} to {arguments['end_date']}):\n\n{json.dumps(project_data, indent=2)}"
                    }
                ]
            }
        else:
            error_msg = f"Failed to get project hours. Status: {response.status_code}, Response: {response.text}"
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
        error_msg = f"Network error when getting project hours: {str(e)}"
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
        error_msg = f"Error getting project hours: {str(e)}"
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
            name="timesheet_entry_template",
            description="Template for adding a timesheet entry",
            arguments=[
                {
                    "name": "employee_id",
                    "description": "Employee ID",
                    "required": True
                },
                {
                    "name": "project",
                    "description": "Project name",
                    "required": True
                }
            ]
        ),
        Prompt(
            name="timesheet_reporting_guide",
            description="Guide for timesheet reporting and best practices"
        )
    ]
    return {"prompts": [prompt.dict() for prompt in prompts]}

@app.post("/mcp/resources/list")
async def list_resources():
    """MCP resources list endpoint"""
    resources = [
        Resource(
            uri="timesheet://projects",
            name="Project Codes",
            description="Available project codes and descriptions",
            mimeType="application/json"
        ),
        Resource(
            uri="timesheet://templates",
            name="Entry Templates",
            description="Common timesheet entry templates",
            mimeType="text/plain"
        ),
        Resource(
            uri="timesheet://policies",
            name="Time Tracking Policies",
            description="Company time tracking policies and procedures",
            mimeType="text/plain"
        )
    ]
    return {"resources": [resource.dict() for resource in resources]}

def main():
    """Main entry point for the web application"""
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting Timesheet MCP Server v2 web application on {host}:{port}")
    logger.info(f"Timesheet API URL: {TIMESHEET_API_URL}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
