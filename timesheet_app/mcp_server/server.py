from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import requests
import os
from datetime import datetime, timedelta

TIMESHEET_API_URL = os.getenv("TIMESHEET_API_URL", "http://localhost:8002")

app = FastAPI(title="Timesheet MCP Server", description="MCP Server for Timesheet Management with Tools, Prompts, and Resources")

class AddEntryPayload(BaseModel):
    employee_id: int
    entry_date: str
    hours: int
    project: str | None = None
    notes: str | None = None

class PromptRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] | None = None

class ResourceRequest(BaseModel):
    uri: str

@app.get("/mcp/health")
def health():
    return {"status": "mcp server ok"}

# ============================================================================
# MCP TOOLS - Actions the server can perform
# ============================================================================

@app.get("/mcp/tools/list")
def list_tools():
    """List all available tools"""
    return {
        "tools": [
            {
                "name": "add_timesheet_entry",
                "description": "Add a timesheet entry for an employee",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "employee_id": {"type": "integer", "description": "Employee ID"},
                        "entry_date": {"type": "string", "description": "Entry date (YYYY-MM-DD)"},
                        "hours": {"type": "integer", "description": "Hours worked"},
                        "project": {"type": "string", "description": "Project name or code"},
                        "notes": {"type": "string", "description": "Optional notes about the work"}
                    },
                    "required": ["employee_id", "entry_date", "hours"]
                }
            },
            {
                "name": "list_timesheet_entries",
                "description": "List timesheet entries for an employee",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "employee_id": {"type": "integer", "description": "Employee ID"}
                    },
                    "required": ["employee_id"]
                }
            }
        ]
    }

@app.post("/mcp/tools/add_timesheet_entry")
def mcp_add_entry(payload: AddEntryPayload):
    r = requests.post(
        f"{TIMESHEET_API_URL}/employees/{payload.employee_id}/entries",
        json={
            "entry_date": payload.entry_date,
            "hours": payload.hours,
            "project": payload.project,
            "notes": payload.notes,
        },
        timeout=10,
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

@app.get("/mcp/tools/list_timesheet_entries")
def mcp_list_entries(employee_id: int):
    r = requests.get(f"{TIMESHEET_API_URL}/employees/{employee_id}/entries", timeout=10)
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

# ============================================================================
# MCP PROMPTS - Pre-defined prompt templates for common tasks
# ============================================================================

@app.get("/mcp/prompts/list")
def list_prompts():
    """List all available prompts"""
    return {
        "prompts": [
            {
                "name": "timesheet_reminder",
                "description": "Generate a friendly reminder about timesheet submission",
                "arguments": [
                    {"name": "employee_name", "description": "Name of the employee", "required": True},
                    {"name": "period_end", "description": "End date of the timesheet period", "required": True},
                    {"name": "missing_days", "description": "Number of missing days", "required": False}
                ]
            },
            {
                "name": "project_time_summary",
                "description": "Create a summary of time spent on projects",
                "arguments": [
                    {"name": "employee_id", "description": "Employee ID for data retrieval", "required": True},
                    {"name": "period", "description": "Period to summarize (week/month)", "required": False},
                    {"name": "project_filter", "description": "Specific project to focus on", "required": False}
                ]
            },
            {
                "name": "overtime_analysis",
                "description": "Analyze overtime patterns and provide recommendations",
                "arguments": [
                    {"name": "employee_id", "description": "Employee ID for analysis", "required": True},
                    {"name": "threshold_hours", "description": "Daily hours threshold for overtime", "required": False}
                ]
            }
        ]
    }

@app.post("/mcp/prompts/get")
def get_prompt(request: PromptRequest):
    """Get a specific prompt with filled arguments"""
    
    if request.name == "timesheet_reminder":
        args = request.arguments or {}
        employee_name = args.get("employee_name", "[Employee Name]")
        period_end = args.get("period_end", "[Period End Date]")
        missing_days = args.get("missing_days", "several")
        
        template = f"""Subject: Timesheet Submission Reminder - Due {period_end}

Hi {employee_name},

I hope you're having a great day! This is a friendly reminder that your timesheet for the period ending {period_end} is due soon.

I noticed you have {missing_days} day(s) that haven't been logged yet. To ensure accurate payroll processing and project tracking, please:

1. Log into the timesheet system
2. Fill in your hours for each day
3. Include project codes where applicable
4. Add brief notes about your work (optional but helpful)
5. Submit before the deadline

If you need help with:
- Project codes: Check with your project manager
- System access: Contact IT support
- Time allocation questions: Reach out to your supervisor

Thanks for keeping our records up to date!

Best regards,
[Your Name]"""

        return {"prompt": template}
    
    elif request.name == "project_time_summary":
        args = request.arguments or {}
        employee_id = args.get("employee_id")
        period = args.get("period", "current period")
        project_filter = args.get("project_filter", "")
        
        # Get actual timesheet data if employee_id provided
        timesheet_data = ""
        if employee_id:
            try:
                entries_response = mcp_list_entries(int(employee_id))
                if entries_response:
                    timesheet_data = "\n\nYour recent timesheet entries:\n"
                    project_totals = {}
                    
                    for entry in entries_response[-10:]:  # Last 10 entries
                        project = entry.get("project", "No Project")
                        hours = entry.get("hours", 0)
                        date = entry.get("entry_date", "")
                        
                        if project_filter and project_filter.lower() not in project.lower():
                            continue
                            
                        if project not in project_totals:
                            project_totals[project] = 0
                        project_totals[project] += hours
                        
                        timesheet_data += f"- {date}: {hours}h on {project}\n"
                    
                    if project_totals:
                        timesheet_data += "\nProject totals:\n"
                        for project, total in project_totals.items():
                            timesheet_data += f"- {project}: {total} hours\n"
            except:
                timesheet_data = "\n\n(Unable to retrieve timesheet data)\n"
        
        filter_text = f" for {project_filter}" if project_filter else ""
        
        template = f"""Project Time Summary{filter_text} - {period}

## Time Allocation Analysis

This summary shows your time distribution across projects{filter_text} for {period}.

### Key Insights
- Review your time allocation across different projects
- Identify which projects are consuming most time
- Ensure billing accuracy for client projects
- Track progress against project budgets

### Recommendations
1. **Time Tracking**: Log time daily for accuracy
2. **Project Codes**: Always use correct project codes
3. **Detailed Notes**: Include specific tasks in notes
4. **Regular Review**: Weekly review of time allocation

### Best Practices
- Record time in 15-minute increments
- Be specific about tasks and achievements
- Note any blockers or delays
- Coordinate with project managers on time expectations{timesheet_data}

For questions about project codes or time allocation, contact your project manager or team lead."""

        return {"prompt": template}
    
    elif request.name == "overtime_analysis":
        args = request.arguments or {}
        employee_id = args.get("employee_id")
        threshold_hours = args.get("threshold_hours", 8)
        
        # Analyze overtime patterns if employee_id provided
        overtime_analysis = ""
        if employee_id:
            try:
                entries_response = mcp_list_entries(int(employee_id))
                if entries_response:
                    overtime_days = 0
                    total_overtime = 0
                    daily_breakdown = []
                    
                    for entry in entries_response[-30:]:  # Last 30 entries
                        hours = entry.get("hours", 0)
                        date = entry.get("entry_date", "")
                        
                        if hours > threshold_hours:
                            overtime = hours - threshold_hours
                            overtime_days += 1
                            total_overtime += overtime
                            daily_breakdown.append(f"- {date}: {hours}h ({overtime}h overtime)")
                    
                    overtime_analysis = f"\n\nYour overtime analysis (last 30 entries):\n"
                    overtime_analysis += f"- Days with overtime: {overtime_days}\n"
                    overtime_analysis += f"- Total overtime hours: {total_overtime}\n"
                    overtime_analysis += f"- Average overtime per day: {total_overtime/max(len(entries_response[-30:]), 1):.1f}h\n"
                    
                    if daily_breakdown:
                        overtime_analysis += "\nOvertime breakdown:\n"
                        overtime_analysis += "\n".join(daily_breakdown[-10:])  # Last 10 overtime days
            except:
                overtime_analysis = "\n\n(Unable to retrieve overtime data)\n"
        
        template = f"""Overtime Analysis Report

## Overview
This analysis examines work patterns exceeding {threshold_hours} hours per day to help maintain work-life balance and identify potential workload issues.

## Health & Productivity Guidelines
- **Recommended daily hours**: {threshold_hours} hours
- **Sustainable overtime**: Maximum 2-3 hours per week
- **Recovery time**: Essential after high-intensity periods

## Warning Signs to Watch
1. **Consistent overtime**: More than 3 days per week
2. **Extended hours**: Regularly working 10+ hours per day
3. **Weekend work**: Regular weekend timesheet entries
4. **Declining productivity**: More hours but same output

## Recommendations
### Immediate Actions
- Review current workload with manager
- Identify tasks that can be delegated or postponed
- Set boundaries for work hours
- Take regular breaks during long days

### Long-term Solutions
- Improve time management skills
- Request additional resources for projects
- Negotiate realistic deadlines
- Consider workload redistribution{overtime_analysis}

## Next Steps
1. Discuss patterns with your manager
2. Identify root causes of overtime
3. Develop strategies to reduce excessive hours
4. Monitor progress weekly

Remember: Sustainable work habits lead to better long-term productivity and job satisfaction."""

        return {"prompt": template}
    
    else:
        raise HTTPException(status_code=404, detail=f"Prompt '{request.name}' not found")

# ============================================================================
# MCP RESOURCES - Data and content the server can provide
# ============================================================================

@app.get("/mcp/resources/list")
def list_resources():
    """List all available resources"""
    return {
        "resources": [
            {
                "uri": "timesheet://policies/submission",
                "name": "Timesheet Submission Policy",
                "description": "Guidelines for timesheet submission and approval",
                "mimeType": "text/plain"
            },
            {
                "uri": "timesheet://codes/projects",
                "name": "Project Code Directory",
                "description": "List of valid project codes and descriptions",
                "mimeType": "application/json"
            },
            {
                "uri": "timesheet://templates/weekly",
                "name": "Weekly Timesheet Template",
                "description": "Standard weekly timesheet template",
                "mimeType": "text/plain"
            },
            {
                "uri": "timesheet://reports/utilization",
                "name": "Team Utilization Report",
                "description": "Current team utilization rates and trends",
                "mimeType": "application/json"
            },
            {
                "uri": "timesheet://guidelines/best-practices",
                "name": "Time Tracking Best Practices",
                "description": "Best practices for accurate time tracking",
                "mimeType": "text/plain"
            }
        ]
    }

@app.post("/mcp/resources/read")
def read_resource(request: ResourceRequest):
    """Read a specific resource"""
    
    if request.uri == "timesheet://policies/submission":
        content = """TIMESHEET SUBMISSION POLICY

1. SUBMISSION REQUIREMENTS
   - Weekly submission by Friday 5:00 PM
   - All days must be accounted for (including PTO, holidays)
   - Minimum time increment: 15 minutes (0.25 hours)
   - Maximum daily hours: 12 (requires manager approval for >10)

2. PROJECT CODES
   - All time must be allocated to valid project codes
   - Use "ADMIN" for administrative tasks
   - Use "TRAIN" for training and development
   - Use "MEET" for general meetings

3. DESCRIPTIONS
   - Brief description required for each entry
   - Include specific tasks or achievements
   - Note any issues or blockers encountered
   - Reference ticket numbers where applicable

4. APPROVAL PROCESS
   - Manager review required within 3 business days
   - Automated approval for regular patterns
   - Special approval needed for overtime
   - Corrections must be resubmitted

5. LATE SUBMISSIONS
   - Grace period: 1 business day after deadline
   - Late fees may apply after grace period
   - Payroll delays possible for extended lateness
   - Manager notification for repeated late submissions"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    elif request.uri == "timesheet://codes/projects":
        project_codes = {
            "updated": datetime.now().isoformat(),
            "projects": [
                {
                    "code": "PROJ001",
                    "name": "Customer Portal Development",
                    "client": "TechCorp Inc",
                    "status": "active",
                    "billable": True
                },
                {
                    "code": "PROJ002", 
                    "name": "Mobile App Redesign",
                    "client": "StartupXYZ",
                    "status": "active",
                    "billable": True
                },
                {
                    "code": "PROJ003",
                    "name": "Internal Tools Maintenance",
                    "client": "Internal",
                    "status": "active",
                    "billable": False
                },
                {
                    "code": "ADMIN",
                    "name": "Administrative Tasks",
                    "client": "Internal",
                    "status": "active",
                    "billable": False
                },
                {
                    "code": "TRAIN",
                    "name": "Training & Development",
                    "client": "Internal", 
                    "status": "active",
                    "billable": False
                },
                {
                    "code": "MEET",
                    "name": "Meetings & Collaboration",
                    "client": "Internal",
                    "status": "active",
                    "billable": False
                }
            ]
        }
        return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(project_codes)}]}
    
    elif request.uri == "timesheet://templates/weekly":
        content = """WEEKLY TIMESHEET TEMPLATE

Employee: _______________  Week Ending: _______________

        | Mon | Tue | Wed | Thu | Fri | Sat | Sun | Total |
--------|-----|-----|-----|-----|-----|-----|-----|-------|
PROJ001 |     |     |     |     |     |     |     |       |
PROJ002 |     |     |     |     |     |     |     |       |
ADMIN   |     |     |     |     |     |     |     |       |
TRAIN   |     |     |     |     |     |     |     |       |
MEET    |     |     |     |     |     |     |     |       |
PTO     |     |     |     |     |     |     |     |       |
--------|-----|-----|-----|-----|-----|-----|-----|-------|
TOTAL   |     |     |     |     |     |     |     |       |

DAILY NOTES:
Monday: ________________________________
Tuesday: _______________________________
Wednesday: _____________________________
Thursday: ______________________________
Friday: ________________________________
Saturday: ______________________________
Sunday: ________________________________

WEEKLY SUMMARY:
Major accomplishments: _________________
_______________________________________

Challenges/Blockers: __________________
______________________________________ 

Employee Signature: ___________  Date: _______
Manager Approval: _____________  Date: _______"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    elif request.uri == "timesheet://reports/utilization":
        # Generate utilization report with real or demo data
        try:
            # Attempt to get real employee data
            employees_response = requests.get(f"{TIMESHEET_API_URL}/employees", timeout=5)
            if employees_response.status_code == 200:
                employees = employees_response.json()
                utilization_report = {
                    "generated_at": datetime.now().isoformat(),
                    "report_period": "Current Week",
                    "team_utilization": []
                }
                
                for emp in employees[:5]:  # Limit to first 5 for demo
                    try:
                        entries_response = requests.get(f"{TIMESHEET_API_URL}/employees/{emp['id']}/entries", timeout=5)
                        if entries_response.status_code == 200:
                            entries = entries_response.json()
                            
                            # Calculate recent utilization (last 7 entries)
                            recent_entries = entries[-7:] if len(entries) >= 7 else entries
                            total_hours = sum(entry.get("hours", 0) for entry in recent_entries)
                            billable_hours = sum(entry.get("hours", 0) for entry in recent_entries 
                                               if entry.get("project", "").startswith("PROJ"))
                            
                            utilization_rate = (billable_hours / max(total_hours, 1)) * 100
                            
                            utilization_report["team_utilization"].append({
                                "employee_id": emp["id"],
                                "name": emp["name"],
                                "total_hours": total_hours,
                                "billable_hours": billable_hours,
                                "utilization_rate": round(utilization_rate, 1),
                                "target_rate": 75.0
                            })
                        else:
                            utilization_report["team_utilization"].append({
                                "employee_id": emp["id"],
                                "name": emp["name"],
                                "total_hours": 0,
                                "billable_hours": 0,
                                "utilization_rate": 0,
                                "target_rate": 75.0
                            })
                    except:
                        pass
                
                return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(utilization_report)}]}
            else:
                raise Exception("API unavailable")
        except:
            # Fallback demo data
            demo_report = {
                "generated_at": datetime.now().isoformat(),
                "report_period": "Current Week",
                "note": "Demo data - API unavailable",
                "team_utilization": [
                    {
                        "employee_id": 1,
                        "name": "John Doe", 
                        "total_hours": 40,
                        "billable_hours": 32,
                        "utilization_rate": 80.0,
                        "target_rate": 75.0
                    },
                    {
                        "employee_id": 2,
                        "name": "Jane Smith",
                        "total_hours": 38,
                        "billable_hours": 28,
                        "utilization_rate": 73.7,
                        "target_rate": 75.0
                    }
                ]
            }
            return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(demo_report)}]}
    
    elif request.uri == "timesheet://guidelines/best-practices":
        content = """TIME TRACKING BEST PRACTICES

1. CONSISTENCY
   - Log time daily, not weekly
   - Use consistent project codes
   - Maintain regular logging habits
   - Set daily reminders if needed

2. ACCURACY
   - Round to nearest 15 minutes
   - Be honest about actual time spent
   - Include breaks and interruptions
   - Track all work-related activities

3. DETAIL LEVEL
   - Include specific task descriptions
   - Reference tickets or requirements
   - Note any blockers or issues
   - Mention tools or technologies used

4. PROJECT ALLOCATION
   - Understand client vs. internal time
   - Ask for clarification on project codes
   - Split time appropriately across projects
   - Don't forget administrative tasks

5. QUALITY OVER QUANTITY
   - Focus on value delivered, not hours logged
   - Include accomplishments in notes
   - Track learning and improvement time
   - Note collaboration and knowledge sharing

6. COMMUNICATION
   - Discuss unclear time allocation with manager
   - Report unusual patterns or overtime
   - Coordinate with team on shared tasks
   - Provide context for unusual entries

7. TOOLS & EFFICIENCY
   - Use timer apps for accuracy
   - Set up project shortcuts
   - Automate recurring entries where possible
   - Review and adjust weekly

REMEMBER: Good time tracking helps with:
- Accurate client billing
- Project planning and estimation
- Resource allocation decisions
- Performance evaluation
- Work-life balance monitoring"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    else:
        raise HTTPException(status_code=404, detail=f"Resource '{request.uri}' not found")
