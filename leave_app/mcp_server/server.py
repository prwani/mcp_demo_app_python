from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any
import requests
import os
from datetime import datetime, timedelta

LEAVE_API_URL = os.getenv("LEAVE_API_URL", "http://localhost:8001")

app = FastAPI(title="Leave MCP Server", description="MCP Server for Leave Management with Tools, Prompts, and Resources")

class ApplyLeavePayload(BaseModel):
    employee_id: int
    start_date: str
    end_date: str
    leave_type: str
    reason: str | None = None

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
                "name": "apply_leave",
                "description": "Apply for leave on behalf of an employee",
                "inputSchema": {
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
            },
            {
                "name": "get_balance",
                "description": "Get leave balance for an employee",
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

@app.post("/mcp/tools/apply_leave")
def mcp_apply_leave(payload: ApplyLeavePayload):
    r = requests.post(
        f"{LEAVE_API_URL}/employees/{payload.employee_id}/leave-requests",
        json={
            "start_date": payload.start_date,
            "end_date": payload.end_date,
            "leave_type": payload.leave_type,
            "reason": payload.reason,
        },
        timeout=10,
    )
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()

@app.get("/mcp/tools/get_balance")
def mcp_get_balance(employee_id: int):
    r = requests.get(f"{LEAVE_API_URL}/employees/{employee_id}/balance", timeout=10)
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
                "name": "leave_request_email",
                "description": "Generate a professional email template for leave requests",
                "arguments": [
                    {"name": "employee_name", "description": "Name of the employee", "required": True},
                    {"name": "start_date", "description": "Leave start date", "required": True},
                    {"name": "end_date", "description": "Leave end date", "required": True},
                    {"name": "leave_type", "description": "Type of leave", "required": True},
                    {"name": "reason", "description": "Reason for leave", "required": False}
                ]
            },
            {
                "name": "leave_policy_summary",
                "description": "Generate a summary of leave policies for an employee",
                "arguments": [
                    {"name": "employee_id", "description": "Employee ID to get current balance", "required": True},
                    {"name": "focus_area", "description": "Specific area to focus on (vacation, sick, etc.)", "required": False}
                ]
            },
            {
                "name": "leave_calendar_planning",
                "description": "Help plan leave requests around holidays and team availability",
                "arguments": [
                    {"name": "month", "description": "Month to plan for (YYYY-MM)", "required": True},
                    {"name": "team_size", "description": "Size of the team", "required": False}
                ]
            }
        ]
    }

@app.post("/mcp/prompts/get")
def get_prompt(request: PromptRequest):
    """Get a specific prompt with filled arguments"""
    
    if request.name == "leave_request_email":
        args = request.arguments or {}
        employee_name = args.get("employee_name", "[Employee Name]")
        start_date = args.get("start_date", "[Start Date]")
        end_date = args.get("end_date", "[End Date]")
        leave_type = args.get("leave_type", "[Leave Type]")
        reason = args.get("reason", "")
        
        reason_text = f"\n\nReason: {reason}" if reason else ""
        
        template = f"""Subject: Leave Request - {employee_name} ({start_date} to {end_date})

Dear [Manager Name],

I would like to request {leave_type} leave from {start_date} to {end_date}.{reason_text}

I will ensure all my current projects are up to date and will coordinate with the team to cover any urgent matters during my absence.

Please let me know if you need any additional information or if there are any concerns with these dates.

Thank you for your consideration.

Best regards,
{employee_name}"""

        return {"prompt": template}
    
    elif request.name == "leave_policy_summary":
        args = request.arguments or {}
        employee_id = args.get("employee_id")
        focus_area = args.get("focus_area", "")
        
        # Get current balance if employee_id provided
        balance_info = ""
        if employee_id:
            try:
                balance_response = mcp_get_balance(int(employee_id))
                balance_info = f"\n\nYour current leave balances:\n"
                for leave_type, days in balance_response.items():
                    if leave_type != "employee_id":
                        balance_info += f"- {leave_type.title()}: {days} days\n"
            except:
                balance_info = "\n\n(Unable to retrieve current balance)\n"
        
        focus_text = f" with focus on {focus_area}" if focus_area else ""
        
        template = f"""Leave Policy Summary{focus_text}

Here's a summary of your leave entitlements and policies:

## Annual Leave
- Standard entitlement: 25 days per year
- Can be carried over: Up to 5 days to next year
- Must be taken: Minimum 10 consecutive days per year

## Sick Leave
- Entitlement: 10 days per year
- No carryover to next year
- Medical certificate required for 3+ consecutive days

## Personal Leave
- Entitlement: 5 days per year
- For personal emergencies and appointments
- Must be approved by manager

## Application Process
1. Submit request at least 2 weeks in advance (except emergencies)
2. Get manager approval
3. Update team calendar
4. Arrange coverage for responsibilities{balance_info}

For specific questions, please contact HR or your manager."""

        return {"prompt": template}
    
    elif request.name == "leave_calendar_planning":
        args = request.arguments or {}
        month = args.get("month", datetime.now().strftime("%Y-%m"))
        team_size = args.get("team_size", "small")
        
        template = f"""Leave Calendar Planning for {month}

## Planning Considerations

### Team Coverage Guidelines
- Team size: {team_size}
- Maximum simultaneous leave: {"1 person" if team_size == "small" else "20% of team"}
- Critical periods: Month-end, project deadlines, team meetings

### Best Practices
1. **Plan Early**: Submit requests 2-4 weeks in advance
2. **Check Holidays**: Coordinate with public holidays for longer breaks
3. **Team Coordination**: Check with colleagues before booking popular periods
4. **Project Deadlines**: Avoid leave during critical project phases

### Monthly Tips for {month}
- Check for public holidays this month
- Consider school holiday periods if you have children
- Plan around quarterly reviews or month-end processes
- Coordinate with team members for optimal coverage

### Action Items
□ Review team calendar for existing bookings
□ Identify your preferred dates
□ Check project deadlines and commitments
□ Submit formal leave request
□ Arrange coverage and handovers

Remember: Early planning leads to better approval rates and less stress for everyone!"""

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
                "uri": "leave://policies/annual",
                "name": "Annual Leave Policy",
                "description": "Complete annual leave policy document",
                "mimeType": "text/plain"
            },
            {
                "uri": "leave://policies/sick", 
                "name": "Sick Leave Policy",
                "description": "Sick leave policy and procedures",
                "mimeType": "text/plain"
            },
            {
                "uri": "leave://forms/application",
                "name": "Leave Application Form",
                "description": "Standard leave application form template",
                "mimeType": "text/plain"
            },
            {
                "uri": "leave://calendar/holidays",
                "name": "Public Holidays Calendar",
                "description": "Current year public holidays list",
                "mimeType": "application/json"
            },
            {
                "uri": "leave://reports/team-status",
                "name": "Team Leave Status",
                "description": "Current leave status for all team members",
                "mimeType": "application/json"
            }
        ]
    }

@app.post("/mcp/resources/read")
def read_resource(request: ResourceRequest):
    """Read a specific resource"""
    
    if request.uri == "leave://policies/annual":
        content = """ANNUAL LEAVE POLICY

1. ENTITLEMENT
   - Full-time employees: 25 days per calendar year
   - Part-time employees: Pro-rated based on hours worked
   - Accrual starts from first day of employment

2. CARRYOVER
   - Maximum 5 days can be carried to next year
   - Must be used within first quarter of new year
   - No cash payment for unused leave

3. APPLICATION PROCESS
   - Submit request minimum 2 weeks in advance
   - Use official leave management system
   - Manager approval required
   - HR notification automatic

4. RESTRICTIONS
   - Maximum 15 consecutive days without special approval
   - No more than 50% of team on leave simultaneously
   - Blackout periods apply during peak business periods

5. PUBLIC HOLIDAYS
   - Do not count against annual leave entitlement
   - If holiday falls during leave period, leave day is credited back"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    elif request.uri == "leave://policies/sick":
        content = """SICK LEAVE POLICY

1. ENTITLEMENT
   - 10 days per calendar year for all employees
   - No carryover to following year
   - Resets on January 1st

2. USAGE
   - For personal illness or injury
   - For medical appointments that cannot be scheduled outside work hours
   - For caring for immediate family members who are ill

3. CERTIFICATION
   - Self-certification for 1-2 days
   - Medical certificate required for 3+ consecutive days
   - Return-to-work certificate may be required

4. NOTIFICATION
   - Notify manager as soon as possible
   - Before start of shift if possible
   - Update daily for extended absences

5. EXTENDED ILLNESS
   - Beyond 10 days moves to long-term disability
   - Contact HR for assistance and options
   - May require independent medical examination"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    elif request.uri == "leave://forms/application":
        content = """LEAVE APPLICATION FORM

Employee Information:
- Name: ________________
- Employee ID: ________________
- Department: ________________
- Manager: ________________

Leave Details:
- Leave Type: [ ] Annual [ ] Sick [ ] Personal [ ] Other: ________
- Start Date: ________________
- End Date: ________________
- Total Days: ________________
- Return Date: ________________

Reason (if applicable):
_________________________________________________
_________________________________________________

Coverage Arrangements:
- Work to be delegated to: ________________
- Emergency contact: ________________
- Email/phone during leave: ________________

Employee Signature: ________________    Date: ________

Manager Approval:
[ ] Approved [ ] Declined [ ] Pending

Manager Comments:
_________________________________________________

Manager Signature: ________________    Date: ________

HR Use Only:
- Leave balance before: ________
- Leave balance after: ________
- Processed by: ________________
- Date: ________"""

        return {"contents": [{"uri": request.uri, "mimeType": "text/plain", "text": content}]}
    
    elif request.uri == "leave://calendar/holidays":
        # Get current year holidays (simplified example)
        current_year = datetime.now().year
        holidays = {
            "year": current_year,
            "holidays": [
                {"date": f"{current_year}-01-01", "name": "New Year's Day"},
                {"date": f"{current_year}-07-04", "name": "Independence Day"},
                {"date": f"{current_year}-12-25", "name": "Christmas Day"},
                {"date": f"{current_year}-11-28", "name": "Thanksgiving"}, # Approximate
                {"date": f"{current_year}-09-02", "name": "Labor Day"}, # Approximate
            ]
        }
        return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(holidays)}]}
    
    elif request.uri == "leave://reports/team-status":
        # This would typically fetch from the API, but for demo purposes:
        try:
            # Attempt to get some real data
            employees_response = requests.get(f"{LEAVE_API_URL}/employees", timeout=5)
            if employees_response.status_code == 200:
                employees = employees_response.json()
                team_status = {
                    "generated_at": datetime.now().isoformat(),
                    "team_members": []
                }
                
                for emp in employees[:5]:  # Limit to first 5 for demo
                    try:
                        balance_response = requests.get(f"{LEAVE_API_URL}/employees/{emp['id']}/balance", timeout=5)
                        requests_response = requests.get(f"{LEAVE_API_URL}/employees/{emp['id']}/leave-requests", timeout=5)
                        
                        balance = balance_response.json() if balance_response.status_code == 200 else {}
                        recent_requests = requests_response.json() if requests_response.status_code == 200 else []
                        
                        # Check for pending or approved future leave
                        upcoming_leave = []
                        for req in recent_requests:
                            if req.get("status") in ["pending", "approved"]:
                                upcoming_leave.append({
                                    "start_date": req.get("start_date"),
                                    "end_date": req.get("end_date"),
                                    "status": req.get("status")
                                })
                        
                        team_status["team_members"].append({
                            "employee_id": emp["id"],
                            "name": emp["name"],
                            "leave_balance": balance,
                            "upcoming_leave": upcoming_leave
                        })
                    except:
                        # If individual employee data fails, include basic info
                        team_status["team_members"].append({
                            "employee_id": emp["id"],
                            "name": emp["name"],
                            "leave_balance": "unavailable",
                            "upcoming_leave": []
                        })
                
                return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(team_status)}]}
            else:
                raise Exception("API unavailable")
        except:
            # Fallback demo data
            demo_status = {
                "generated_at": datetime.now().isoformat(),
                "note": "Demo data - API unavailable",
                "team_members": [
                    {
                        "employee_id": 1,
                        "name": "John Doe",
                        "leave_balance": {"vacation": 15, "sick": 8, "personal": 3},
                        "upcoming_leave": [{"start_date": "2025-09-01", "end_date": "2025-09-05", "status": "approved"}]
                    },
                    {
                        "employee_id": 2, 
                        "name": "Jane Smith",
                        "leave_balance": {"vacation": 20, "sick": 10, "personal": 5},
                        "upcoming_leave": []
                    }
                ]
            }
            return {"contents": [{"uri": request.uri, "mimeType": "application/json", "text": str(demo_status)}]}
    
    else:
        raise HTTPException(status_code=404, detail=f"Resource '{request.uri}' not found")
