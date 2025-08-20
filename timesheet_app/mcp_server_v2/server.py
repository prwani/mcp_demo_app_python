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
logger = logging.getLogger("timesheet-mcp-v2")

# Environment configuration
TIMESHEET_API_URL = os.getenv("TIMESHEET_API_URL", "http://localhost:8002")

class TimesheetMcpServer:
    def __init__(self):
        self.app = Server("timesheet-mcp-v2")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up all MCP handlers"""
        
        @self.app.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available timesheet management tools"""
            return ListToolsResult(
                tools=[
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
            )
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Execute timesheet management tools"""
            try:
                if name == "add_timesheet_entry":
                    return await self._add_timesheet_entry(arguments)
                elif name == "get_timesheet_summary":
                    return await self._get_timesheet_summary(arguments)
                elif name == "get_project_hours":
                    return await self._get_project_hours(arguments)
                else:
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Tool {name} not found")
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                raise McpError(ErrorCode.INTERNAL_ERROR, f"Tool execution failed: {str(e)}")

        @self.app.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            """List available prompts for timesheet management"""
            return ListPromptsResult(
                prompts=[
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
                        description="Guide for timesheet reporting and best practices",
                        arguments=[
                            {
                                "name": "report_type",
                                "description": "Type of report needed",
                                "required": False
                            }
                        ]
                    ),
                    Prompt(
                        name="weekly_timesheet_reminder",
                        description="Weekly timesheet submission reminder",
                        arguments=[
                            {
                                "name": "week_ending",
                                "description": "Week ending date",
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
                if name == "timesheet_entry_template":
                    employee_id = arguments.get("employee_id", "[EMPLOYEE_ID]") if arguments else "[EMPLOYEE_ID]"
                    project = arguments.get("project", "[PROJECT_NAME]") if arguments else "[PROJECT_NAME]"
                    
                    template = f"""
Timesheet Entry Template

Employee ID: {employee_id}
Date: [YYYY-MM-DD]
Project: {project}
Hours: [Number of hours worked]
Description: [Brief description of work performed]

Instructions:
1. Fill in all required fields
2. Ensure date is in YYYY-MM-DD format
3. Hours should be decimal (e.g., 7.5 for 7 hours 30 minutes)
4. Use standard project codes or names
5. Provide clear, concise work description
6. Submit using the add_timesheet_entry tool

Example:
- Date: 2024-08-17
- Hours: 8.0
- Project: WEB-2024-001
- Description: Frontend development for user dashboard

Tips:
- Log time daily for accuracy
- Include both development and meeting time
- Reference ticket numbers when applicable
"""
                    return GetPromptResult(
                        description="Template for adding a timesheet entry",
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
                
                elif name == "timesheet_reporting_guide":
                    report_type = arguments.get("report_type", "general") if arguments else "general"
                    
                    guide = """
Timesheet Reporting Guide

DAILY PRACTICES:
- Log time at the end of each workday
- Record actual hours worked, not scheduled hours
- Use specific project codes and clear descriptions
- Include meetings, training, and administrative time

WEEKLY SUBMISSION:
- Submit timesheets by end of business Friday
- Review weekly totals for accuracy
- Ensure all projects are properly categorized
- Include any overtime or special circumstances

MONTHLY REPORTING:
- Use get_timesheet_summary tool for monthly reports
- Review project hour allocations
- Check for any missing or incomplete entries
- Validate total hours against expected workload

PROJECT TRACKING:
- Use get_project_hours tool for project analysis
- Track time against project budgets
- Monitor resource allocation efficiency
- Report project timeline impacts

BEST PRACTICES:
- Be accurate and honest with time reporting
- Use consistent project naming conventions
- Include context in work descriptions
- Communicate any issues or discrepancies promptly

TOOLS AVAILABLE:
- add_timesheet_entry: Log daily work hours
- get_timesheet_summary: Generate employee summaries
- get_project_hours: Analyze project time allocation
"""
                    return GetPromptResult(
                        description="Guide for timesheet reporting and best practices",
                        messages=[
                            {
                                "role": "assistant",
                                "content": {
                                    "type": "text",
                                    "text": guide
                                }
                            }
                        ]
                    )
                
                elif name == "weekly_timesheet_reminder":
                    week_ending = arguments.get("week_ending", datetime.now().strftime("%Y-%m-%d")) if arguments else datetime.now().strftime("%Y-%m-%d")
                    
                    reminder = f"""
Weekly Timesheet Reminder

Week Ending: {week_ending}

ACTION REQUIRED:
Please ensure your timesheet is complete and submitted for the week ending {week_ending}.

CHECKLIST:
□ All workdays have time entries
□ Project codes are accurate
□ Work descriptions are clear and specific
□ Total hours are reasonable and accurate
□ Any overtime is properly documented
□ Time off or holidays are correctly marked

SUBMISSION DEADLINE:
End of business on Friday

HOW TO CHECK:
Use the get_timesheet_summary tool to review your entries for this period.

NEED HELP?
- Use timesheet_entry_template for proper formatting
- Refer to timesheet_reporting_guide for best practices
- Contact your manager for project code clarification

Remember: Accurate time tracking helps with project planning and resource allocation.
"""
                    return GetPromptResult(
                        description="Weekly timesheet submission reminder",
                        messages=[
                            {
                                "role": "assistant",
                                "content": {
                                    "type": "text",
                                    "text": reminder
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
            )

        @self.app.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read resource content"""
            try:
                if uri == "timesheet://projects":
                    projects = {
                        "active_projects": [
                            {
                                "code": "WEB-2024-001",
                                "name": "Customer Portal Redesign",
                                "description": "Frontend redesign of customer portal",
                                "status": "active",
                                "budget_hours": 500
                            },
                            {
                                "code": "API-2024-002",
                                "name": "Integration API Development",
                                "description": "REST API for third-party integrations",
                                "status": "active",
                                "budget_hours": 300
                            },
                            {
                                "code": "MAINT-2024",
                                "name": "System Maintenance",
                                "description": "Ongoing system maintenance and support",
                                "status": "ongoing",
                                "budget_hours": 1000
                            }
                        ],
                        "administrative_codes": [
                            {
                                "code": "MEETING",
                                "name": "Meetings and Collaboration",
                                "description": "Team meetings, client calls, planning sessions"
                            },
                            {
                                "code": "TRAINING",
                                "name": "Training and Development",
                                "description": "Professional development, learning new technologies"
                            },
                            {
                                "code": "ADMIN",
                                "name": "Administrative Tasks",
                                "description": "HR activities, performance reviews, documentation"
                            }
                        ],
                        "last_updated": datetime.now().isoformat()
                    }
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=json.dumps(projects, indent=2)
                            )
                        ]
                    )
                
                elif uri == "timesheet://templates":
                    templates = """
COMMON TIMESHEET ENTRY TEMPLATES

Development Work:
- Project: [PROJECT_CODE]
- Description: "Implemented [feature/component] for [module/system]"
- Example: "Implemented user authentication for customer portal"

Bug Fixes:
- Project: [PROJECT_CODE]
- Description: "Fixed [bug description] in [component/module]"
- Example: "Fixed login timeout issue in authentication service"

Meetings:
- Project: MEETING
- Description: "[Meeting type] - [purpose/topic]"
- Example: "Sprint planning - Customer portal requirements review"

Code Review:
- Project: [PROJECT_CODE]
- Description: "Code review for [feature/pull request]"
- Example: "Code review for user profile management feature"

Testing:
- Project: [PROJECT_CODE]
- Description: "Testing [feature/component] - [test type]"
- Example: "Testing payment integration - unit and integration tests"

Documentation:
- Project: [PROJECT_CODE]
- Description: "Documentation for [feature/API/process]"
- Example: "API documentation for integration endpoints"

Training:
- Project: TRAINING
- Description: "[Training topic/technology]"
- Example: "React advanced patterns workshop"

Research:
- Project: [PROJECT_CODE]
- Description: "Research [technology/solution] for [purpose]"
- Example: "Research database optimization strategies for performance"
"""
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=templates
                            )
                        ]
                    )
                
                elif uri == "timesheet://policies":
                    policies = """
TIME TRACKING POLICIES AND PROCEDURES

1. GENERAL REQUIREMENTS
   - All work time must be accurately recorded
   - Timesheets must be submitted weekly by Friday EOB
   - Minimum entry: 0.25 hours (15 minutes)
   - Maximum daily hours: 12 hours (requires approval)

2. PROJECT TIME ALLOCATION
   - Use correct project codes for all billable work
   - Administrative time should use appropriate admin codes
   - Meeting time counts toward project if project-specific
   - Training time should be logged under TRAINING code

3. OVERTIME POLICY
   - Hours over 40 per week require manager approval
   - Overtime must be pre-approved when possible
   - Emergency overtime should be documented with explanation
   - Comp time may be available in lieu of overtime pay

4. TIME OFF INTEGRATION
   - Vacation and sick time should not be logged in timesheets
   - Use HR system for time off requests
   - Holidays are automatically excluded from timesheet requirements
   - Partial day absences should be reflected in timesheet hours

5. ACCURACY AND COMPLIANCE
   - Time should be logged daily for best accuracy
   - Estimated time is acceptable if logged within 48 hours
   - Corrections require manager approval for previous weeks
   - Fraudulent time reporting is grounds for disciplinary action

6. PROJECT BUDGET TRACKING
   - Monitor project hour budgets regularly
   - Report potential overruns immediately
   - Use get_project_hours tool for budget analysis
   - Coordinate with project managers on time allocation

7. REPORTING AND ANALYTICS
   - Weekly summaries available via get_timesheet_summary
   - Project reports available via get_project_hours
   - Monthly reports generated automatically
   - Annual time tracking analysis provided to management

8. SUPPORT AND ASSISTANCE
   - Contact HR for policy questions
   - Contact IT for technical timesheet issues
   - Project managers can assist with project code questions
   - Training available for new timesheet system users
"""
                    return ReadResourceResult(
                        contents=[
                            TextContent(
                                type="text",
                                text=policies
                            )
                        ]
                    )
                else:
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Resource {uri} not found")
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {str(e)}")
                raise McpError(ErrorCode.INTERNAL_ERROR, f"Resource reading failed: {str(e)}")

    async def _add_timesheet_entry(self, arguments: Dict[str, Any]) -> CallToolResult:
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
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Timesheet entry added successfully!\n\nDetails:\n{json.dumps(result, indent=2)}"
                        )
                    ]
                )
            else:
                error_msg = f"Failed to add timesheet entry. Status: {response.status_code}, Response: {response.text}"
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
            error_msg = f"Network error when adding timesheet entry: {str(e)}"
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
            error_msg = f"Error adding timesheet entry: {str(e)}"
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

    async def _get_timesheet_summary(self, arguments: Dict[str, Any]) -> CallToolResult:
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
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Timesheet summary for employee {arguments['employee_id']} ({arguments['start_date']} to {arguments['end_date']}):\n\n{json.dumps(summary_data, indent=2)}"
                        )
                    ]
                )
            else:
                error_msg = f"Failed to get timesheet summary. Status: {response.status_code}, Response: {response.text}"
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
            error_msg = f"Network error when getting timesheet summary: {str(e)}"
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
            error_msg = f"Error getting timesheet summary: {str(e)}"
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

    async def _get_project_hours(self, arguments: Dict[str, Any]) -> CallToolResult:
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
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Project hours for {arguments['project']} ({arguments['start_date']} to {arguments['end_date']}):\n\n{json.dumps(project_data, indent=2)}"
                        )
                    ]
                )
            else:
                error_msg = f"Failed to get project hours. Status: {response.status_code}, Response: {response.text}"
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
            error_msg = f"Network error when getting project hours: {str(e)}"
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
            error_msg = f"Error getting project hours: {str(e)}"
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
    parser = argparse.ArgumentParser(description="Timesheet MCP Server v2")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                       help="Transport method (stdio for local, sse for web)")
    parser.add_argument("--host", default="localhost", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=8004, help="Port for SSE transport")
    args = parser.parse_args()

    # Create server instance
    server = TimesheetMcpServer()
    
    if args.transport == "sse":
        # SSE transport for web deployment
        logger.info(f"Starting Timesheet MCP Server v2 with SSE transport on {args.host}:{args.port}")
        transport = SseServerTransport(f"http://{args.host}:{args.port}/sse")
    else:
        # STDIO transport for local usage
        logger.info("Starting Timesheet MCP Server v2 with STDIO transport")
        transport = StdioServerTransport()

    # Run the server
    async with transport:
        await server.app.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
