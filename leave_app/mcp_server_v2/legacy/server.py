import asyncio
import json
import os
import logging
from typing import Any, Dict, List, Optional, Union, Sequence
from datetime import datetime, timedelta

import requests
from mcp.server import Server
from mcp.types import (
    Resource, Tool, Prompt, TextContent, CallToolRequest, CallToolResult,
    GetPromptRequest, GetPromptResult, ReadResourceRequest, ReadResourceResult,
    ListResourcesRequest, ListResourcesResult, ListToolsRequest, ListToolsResult,
    ListPromptsRequest, ListPromptsResult, McpError, ErrorCode
)
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import StdioServerTransport
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leave-mcp-v2")

# Environment configuration
LEAVE_API_URL = os.getenv("LEAVE_API_URL", "http://localhost:8001")

class LeaveMcpServer:
    def __init__(self):
        self.app = Server("leave-mcp-v2")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up all MCP handlers"""
        
        @self.app.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available leave management tools"""
            return ListToolsResult(
                tools=[
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
            )
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute leave management tools"""
            try:
                if name == "apply_leave":
                    return await self._apply_leave(arguments)
                elif name == "get_balance":
                    return await self._get_balance(arguments)
                else:
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Tool {name} not found")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                raise McpError(ErrorCode.INTERNAL_ERROR, f"Tool execution failed: {str(e)}")

        @self.app.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available prompts for leave management"""
            return ListPromptsResult(
                prompts=[
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
                        description="Guidance on leave policies and procedures",
                        arguments=[
                            {
                                "name": "policy_type",
                                "description": "Type of policy information needed",
                                "required": False
                            }
                        ]
                    )
                ]
            )

        @self.app.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
            """Get prompt content"""
            try:
                if name == "leave_application_template":
                    employee_id = arguments.get("employee_id", "[EMPLOYEE_ID]") if arguments else "[EMPLOYEE_ID]"
                    leave_type = arguments.get("leave_type", "[LEAVE_TYPE]") if arguments else "[LEAVE_TYPE]"
                    
                    template = f"""
Leave Application Template

Employee ID: {employee_id}
Leave Type: {leave_type}
Start Date: [YYYY-MM-DD]
End Date: [YYYY-MM-DD]
Reason: [Optional reason for leave]

Instructions:
1. Fill in all required fields
2. Ensure dates are in YYYY-MM-DD format
3. Select appropriate leave type: vacation, sick, or personal
4. Provide a brief reason if needed
5. Submit using the apply_leave tool

Note: Check your leave balance first using the get_balance tool.
"""
                    return GetPromptResult(
                        description="Template for submitting a leave application",
                        messages=[
                            {
                                "role": "user",
                                "content": {
                                    "type": "text",
                                    "text": template
                                }
                            }
                        ]
                    )
                
                elif name == "leave_policy_guidance":
                    policy_type = arguments.get("policy_type", "general") if arguments else "general"
                    
                    guidance = """
Leave Policy Guidance

General Policies:
- Vacation leave: 20 days per year, can be carried over up to 5 days
- Sick leave: 10 days per year, requires medical certificate for >3 consecutive days
- Personal leave: 5 days per year, advance notice required

Application Process:
1. Check your current leave balance
2. Submit application at least 2 weeks in advance for vacation
3. For sick leave, notify as soon as possible
4. Approval is subject to business requirements and coverage

Important Notes:
- Leave requests during peak periods may require additional approval
- Emergency leave can be applied retroactively with proper documentation
- Unused vacation days may expire at year-end (check company policy)

Use the leave management tools to:
- Check your balance: get_balance tool
- Apply for leave: apply_leave tool
"""
                    return GetPromptResult(
                        description="Guidance on leave policies and procedures",
                        messages=[
                            {
                                "role": "assistant",
                                "content": {
                                    "type": "text",
                                    "text": guidance
                                }
                            }
                        ]
                    )
                else:
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Prompt {name} not found")
            except Exception as e:
                logger.error(f"Error getting prompt {name}: {str(e)}")
                raise McpError(ErrorCode.INTERNAL_ERROR, f"Prompt retrieval failed: {str(e)}")

        @self.app.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available resources"""
            return ListResourcesResult(
                resources=[
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
            )

        @self.app.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read resource content"""
            try:
                if uri == "leave://policies":
                    policies = """
LEAVE POLICIES AND PROCEDURES

1. VACATION LEAVE
   - Annual allocation: 20 days
   - Carry-over limit: 5 days maximum
   - Advance notice: 2 weeks minimum
   - Peak period restrictions apply

2. SICK LEAVE
   - Annual allocation: 10 days
   - Medical certificate required for >3 consecutive days
   - Can be applied retroactively with documentation
   - Family sick leave included

3. PERSONAL LEAVE
   - Annual allocation: 5 days
   - Advance notice required
   - Subject to business needs
   - Emergency situations considered

4. APPLICATION PROCESS
   - Use leave management system
   - Manager approval required
   - HR notification automatic
   - Calendar integration available

5. IMPORTANT NOTES
   - Leave year: January 1 - December 31
   - Unused vacation may expire
   - Public holidays don't count as leave
   - Part-time employees: pro-rated allocation
"""
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=policies
                            )
                        ]
                    )
                
                elif uri == "leave://balance/recent":
                    # This would typically come from a cache or recent queries log
                    recent_data = {
                        "recent_queries": [
                            {
                                "employee_id": "example",
                                "timestamp": datetime.now().isoformat(),
                                "balance_type": "vacation",
                                "note": "This is example data - actual queries would be logged here"
                            }
                        ],
                        "last_updated": datetime.now().isoformat()
                    }
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=json.dumps(recent_data, indent=2)
                            )
                        ]
                    )
                else:
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Resource {uri} not found")
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {str(e)}")
                raise McpError(ErrorCode.INTERNAL_ERROR, f"Resource reading failed: {str(e)}")

    async def _apply_leave(self, arguments: Dict[str, Any]) -> CallToolResult:
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
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Leave application submitted successfully!\n\nDetails:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            else:
                error_msg = f"Failed to apply leave. Status: {response.status_code}, Response: {response.text}"
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=error_msg
                        )
                    ],
                    isError=True
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error when applying leave: {str(e)}"
            logger.error(error_msg)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_msg
                    )
                ],
                isError=True
            )
        except Exception as e:
            error_msg = f"Error applying leave: {str(e)}"
            logger.error(error_msg)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_msg
                    )
                ],
                isError=True
            )

    async def _get_balance(self, arguments: Dict[str, Any]) -> CallToolResult:
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
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Leave balance for employee {employee_id}:\n\n{json.dumps(balance_data, indent=2)}"
                        )
                    ]
                )
            else:
                error_msg = f"Failed to get balance. Status: {response.status_code}, Response: {response.text}"
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=error_msg
                        )
                    ],
                    isError=True
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error when getting balance: {str(e)}"
            logger.error(error_msg)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_msg
                    )
                ],
                isError=True
            )
        except Exception as e:
            error_msg = f"Error getting balance: {str(e)}"
            logger.error(error_msg)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=error_msg
                    )
                ],
                isError=True
            )

async def main():
    """Main entry point for the MCP server"""
    parser = argparse.ArgumentParser(description="Leave MCP Server v2")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                       help="Transport method (stdio for local, sse/streamable-http for web)")
    parser.add_argument("--host", default="localhost", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=8003, help="Port for SSE transport")
    args = parser.parse_args()

    # Create server instance
    server = LeaveMcpServer()
    
    if args.transport == "sse":
        # Streamable HTTP transport for web deployment (endpoint exposed at /mcp)
        logger.info(f"Starting Leave MCP Server v2 with streamable HTTP transport on {args.host}:{args.port}")
        transport = SseServerTransport(f"http://{args.host}:{args.port}/mcp")
    else:
        # STDIO transport for local usage
        logger.info("Starting Leave MCP Server v2 with STDIO transport")
        transport = StdioServerTransport()

    # Run the server
    async with transport:
        await server.app.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
