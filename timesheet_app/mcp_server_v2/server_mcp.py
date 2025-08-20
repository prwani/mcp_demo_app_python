"""
Timesheet Management MCP Server v2
A Model Context Protocol compliant server for timesheet management using FastMCP.
"""

import os
import logging
import requests
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("timesheet-mcp-v2")

# Environment configuration: derive default from SUFFIX
_suffix = os.getenv("SUFFIX")
_default_timesheet_api = (
    f"https://mcp-timesheet-api-{_suffix}.azurewebsites.net" if _suffix else "https://mcp-timesheet-api-1234.azurewebsites.net"
)
TIMESHEET_API_URL = os.getenv("TIMESHEET_API_URL", _default_timesheet_api)

# Create FastMCP server
mcp = FastMCP(
    name="Timesheet Management Server v2",
    instructions="A comprehensive timesheet management system that allows employees to add timesheet entries, get summaries, and track project hours. This server provides tools for time tracking and reporting."
)

# Pydantic models for structured responses
class TimesheetEntry(BaseModel):
    """Timesheet entry response structure."""
    employee_id: int = Field(description="Employee ID")
    date: str = Field(description="Work date (YYYY-MM-DD)")
    hours: float = Field(description="Number of hours worked")
    project: str = Field(description="Project name or code")
    description: str = Field(description="Description of work performed")
    entry_id: str = Field(description="Unique entry identifier")

class TimesheetSummary(BaseModel):
    """Timesheet summary response structure."""
    employee_id: int = Field(description="Employee ID")
    start_date: str = Field(description="Summary start date")
    end_date: str = Field(description="Summary end date")
    total_hours: float = Field(description="Total hours worked in period")
    project_breakdown: Dict[str, float] = Field(description="Hours per project")
    entries_count: int = Field(description="Number of timesheet entries")

class ProjectHours(BaseModel):
    """Project hours response structure."""
    project: str = Field(description="Project name or code")
    start_date: str = Field(description="Period start date")
    end_date: str = Field(description="Period end date")
    total_hours: float = Field(description="Total hours worked on project")
    contributors: Dict[str, float] = Field(description="Hours per contributor")
    entries_count: int = Field(description="Number of entries for project")

@mcp.tool()
def add_timesheet_entry(
    employee_id: int,
    date: str,
    hours: float,
    project: str,
    description: str
) -> TimesheetEntry:
    """
    Add a timesheet entry for an employee.
    
    Args:
        employee_id: The ID of the employee
        date: Work date in YYYY-MM-DD format
        hours: Number of hours worked (can be decimal)
        project: Project name or code
        description: Description of work performed
    
    Returns:
        TimesheetEntry: Details of the created timesheet entry
    """
    try:
        # Prepare request data
        entry_data = {
            "employee_id": employee_id,
            "date": date,
            "hours": float(hours),
            "project": project,
            "description": description
        }
        
        logger.info(f"Adding timesheet entry: {entry_data}")
        
        # Make API call
        response = requests.post(
            f"{TIMESHEET_API_URL}/timesheet",
            json=entry_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return TimesheetEntry(
                employee_id=employee_id,
                date=date,
                hours=hours,
                project=project,
                description=description,
                entry_id=result.get("id", "N/A")
            )
        else:
            logger.error(f"Timesheet entry failed: {response.status_code} - {response.text}")
            raise Exception(f"Timesheet entry failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error adding timesheet entry: {e}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding timesheet entry: {e}")
        raise Exception(f"Error adding timesheet entry: {str(e)}")

@mcp.tool()
def get_timesheet_summary(
    employee_id: int,
    start_date: str,
    end_date: str
) -> TimesheetSummary:
    """
    Get timesheet summary for an employee for a specific period.
    
    Args:
        employee_id: The ID of the employee
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        TimesheetSummary: Summary of timesheet data for the period
    """
    try:
        logger.info(f"Getting timesheet summary for employee {employee_id} from {start_date} to {end_date}")
        
        # Make API call
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.get(
            f"{TIMESHEET_API_URL}/timesheet/{employee_id}/summary",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return TimesheetSummary(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                total_hours=result.get("total_hours", 0.0),
                project_breakdown=result.get("project_breakdown", {}),
                entries_count=result.get("entries_count", 0)
            )
        else:
            logger.error(f"Timesheet summary failed: {response.status_code} - {response.text}")
            raise Exception(f"Timesheet summary failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting timesheet summary: {e}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting timesheet summary: {e}")
        raise Exception(f"Error getting timesheet summary: {str(e)}")

@mcp.tool()
def get_project_hours(
    project: str,
    start_date: str,
    end_date: str
) -> ProjectHours:
    """
    Get total hours worked on a specific project.
    
    Args:
        project: Project name or code
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    
    Returns:
        ProjectHours: Total hours and breakdown for the project
    """
    try:
        logger.info(f"Getting project hours for {project} from {start_date} to {end_date}")
        
        # Make API call
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = requests.get(
            f"{TIMESHEET_API_URL}/project/{project}/hours",
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return ProjectHours(
                project=project,
                start_date=start_date,
                end_date=end_date,
                total_hours=result.get("total_hours", 0.0),
                contributors=result.get("contributors", {}),
                entries_count=result.get("entries_count", 0)
            )
        else:
            logger.error(f"Project hours query failed: {response.status_code} - {response.text}")
            raise Exception(f"Project hours query failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting project hours: {e}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting project hours: {e}")
        raise Exception(f"Error getting project hours: {str(e)}")

@mcp.resource("timesheet://employee/{employee_id}/entries")
def get_employee_entries(employee_id: str) -> str:
    """
    Get timesheet entries for a specific employee.
    
    Args:
        employee_id: Employee ID to get entries for
    
    Returns:
        JSON string containing the employee's timesheet entries
    """
    try:
        response = requests.get(
            f"{TIMESHEET_API_URL}/timesheet/{employee_id}/entries",
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            return f'{{"error": "Failed to get entries for employee {employee_id}"}}'
            
    except Exception as e:
        return f'{{"error": "Error getting entries: {str(e)}"}}'

@mcp.resource("timesheet://projects")
def get_project_list() -> str:
    """
    Get list of all active projects.
    
    Returns:
        JSON string containing available projects
    """
    try:
        response = requests.get(
            f"{TIMESHEET_API_URL}/projects",
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            # Return default project list if API fails
            projects = {
                "projects": [
                    {"code": "PROJ-001", "name": "Website Redesign", "status": "active"},
                    {"code": "PROJ-002", "name": "Mobile App Development", "status": "active"},
                    {"code": "PROJ-003", "name": "Database Migration", "status": "active"},
                    {"code": "ADMIN", "name": "Administrative Tasks", "status": "active"},
                    {"code": "TRAINING", "name": "Professional Development", "status": "active"}
                ]
            }
            import json
            return json.dumps(projects, indent=2)
            
    except Exception as e:
        # Return default project list on error
        projects = {
            "projects": [
                {"code": "PROJ-001", "name": "Website Redesign", "status": "active"},
                {"code": "ADMIN", "name": "Administrative Tasks", "status": "active"}
            ],
            "error": f"Error getting projects: {str(e)}"
        }
        import json
        return json.dumps(projects, indent=2)

@mcp.resource("timesheet://policies")
def get_timesheet_policies() -> str:
    """
    Get company timesheet policies and guidelines.
    
    Returns:
        JSON string containing timesheet policies
    """
    policies = {
        "submission_deadline": {
            "description": "Weekly timesheet submission deadline",
            "deadline": "Every Friday by 5:00 PM",
            "late_submission": "Requires manager approval"
        },
        "minimum_time_unit": {
            "description": "Minimum time that can be logged",
            "unit": "0.25 hours (15 minutes)",
            "rounding": "Round to nearest quarter hour"
        },
        "project_codes": {
            "description": "How to use project codes",
            "format": "Use official project codes from the project list",
            "requirement": "All entries must have valid project codes"
        },
        "description_requirements": {
            "description": "Description field requirements",
            "minimum_length": "At least 10 characters describing work performed",
            "examples": ["Developed user authentication module", "Client meeting for requirements gathering"]
        },
        "corrections": {
            "description": "How to correct timesheet entries",
            "same_week": "Can edit entries for current week",
            "previous_weeks": "Requires manager approval for changes"
        }
    }
    
    import json
    return json.dumps(policies, indent=2)

@mcp.prompt()
def timesheet_entry_template(employee_name: str, project: str = "PROJ-001") -> str:
    """
    Generate a timesheet entry template.
    
    Args:
        employee_name: Name of the employee
        project: Project code or name
    
    Returns:
        A formatted timesheet entry template
    """
    return f"""
Timesheet Entry Template for {employee_name}

Date: [YYYY-MM-DD]
Project: {project}
Hours: [Number of hours worked, e.g., 8.0 or 7.5]
Description: [Detailed description of work performed]

Examples of good descriptions:
- "Developed user authentication module for login system"
- "Client meeting to review project requirements and gather feedback"
- "Code review and testing of payment processing feature"
- "Database schema design and optimization for reporting module"

Remember:
- Use quarter-hour increments (0.25, 0.5, 0.75, etc.)
- Be specific about what work was accomplished
- Include project context where relevant
- Submit by Friday 5:00 PM for the current week
    """

@mcp.prompt()
def timesheet_reporting_guide() -> str:
    """
    Generate a guide for timesheet reporting and best practices.
    
    Returns:
        A comprehensive guide for timesheet reporting
    """
    return """
Timesheet Reporting Best Practices Guide

1. DAILY TRACKING
   - Log time daily rather than waiting until end of week
   - Note specific accomplishments and tasks completed
   - Track time as you work for accuracy

2. PROJECT CODES
   - Always use official project codes from the approved list
   - Contact your manager if unsure about correct project code
   - Use ADMIN for administrative tasks, TRAINING for learning

3. DESCRIPTIONS
   - Write clear, specific descriptions (minimum 10 characters)
   - Include what was accomplished, not just "worked on project"
   - Mention deliverables, meetings, or milestones achieved

4. TIME ACCURACY
   - Round to nearest quarter hour (0.25 increments)
   - Account for all work time including meetings and calls
   - Don't forget to log time for code reviews and documentation

5. SUBMISSION DEADLINES
   - Submit weekly timesheets by Friday 5:00 PM
   - Late submissions require manager approval
   - Plan ahead for holiday weeks and vacation schedules

6. CORRECTIONS
   - Current week entries can be edited directly
   - Previous week changes need manager approval
   - Contact HR for timesheet questions or technical issues

For questions about timesheet policies or procedures, contact your direct manager or HR department.
    """

def main():
    """Main entry point for the MCP server."""
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting Timesheet MCP Server v2 on port {port}")
    logger.info(f"Timesheet API URL: {TIMESHEET_API_URL}")
    logger.info(f"Server name: {mcp.name}")
    
    # Configure server settings
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    
    # Run the server with Streamable HTTP transport for better MCP Inspector compatibility
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
