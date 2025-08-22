"""
Leave Management MCP Server v2
A Model Context Protocol compliant server for leave management using FastMCP.
Adds structured logging for easier troubleshooting.
Supports only 'annual' and 'sick' leave types and balances.
"""

import os
import logging
import requests
import time
import json
import uuid
from typing import Any, Literal, cast

# Supported MCP transports type alias (module scope to satisfy type checkers)
TransportType = Literal["stdio", "sse", "streamable-http"]
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging (level and format via env)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logger = logging.getLogger("leave-mcp-v2")

# Make HTTP timeout configurable
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

# Reduce noisy logs unless DEBUG
if LOG_LEVEL == "DEBUG":
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
else:
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def _new_cid() -> str:
    """Generate a short correlation id for tracing across logs."""
    return uuid.uuid4().hex[:8]

def _truncate(s: str, limit: int = 1000) -> str:
    """Truncate long strings for safe logging."""
    if s is None:
        return ""
    return s if len(s) <= limit else s[:limit] + "...<truncated>"

def _safe_json(obj: Any, limit: int = 1000) -> str:
    try:
        return _truncate(json.dumps(obj, ensure_ascii=False), limit)
    except Exception:
        return _truncate(str(obj), limit)

# Environment configuration: construct default from SUFFIX if provided
_suffix = os.getenv("SUFFIX")
_default_leave_api = (
    f"https://mcp-leave-api-{_suffix}.azurewebsites.net" if _suffix else "https://mcp-leave-api-1234.azurewebsites.net"
)
LEAVE_API_URL = os.getenv("LEAVE_API_URL", _default_leave_api)

# Create FastMCP server
mcp = FastMCP(
    name="Leave Management Server v2",
    instructions="A leave management system for applying for leave and checking balances. Only 'annual' and 'sick' leave types are supported."
)

# Pydantic models for structured responses
class LeaveApplication(BaseModel):
    """Leave application response structure."""
    employee_id: int = Field(description="Employee ID")
    start_date: str = Field(description="Leave start date (YYYY-MM-DD)")
    end_date: str = Field(description="Leave end date (YYYY-MM-DD)")
    leave_type: Literal["annual", "sick"] = Field(description="Type of leave (annual or sick)")
    reason: str = Field(description="Reason for leave")
    status: str = Field(description="Application status")
    application_id: int = Field(description="Unique application identifier")

class LeaveBalance(BaseModel):
    """Leave balance response structure (only annual and sick)."""
    employee_id: int = Field(description="Employee ID")
    annual_balance: int = Field(description="Annual leave days remaining")
    sick_balance: int = Field(description="Sick leave days remaining")

@mcp.tool()
def apply_leave(
    employee_id: int,
    start_date: str,
    end_date: str,
    leave_type: Literal["annual", "sick"],
    reason: str = ""
) -> LeaveApplication:
    """
    Apply for leave for an employee.

    Args:
        employee_id: The ID of the employee applying for leave
        start_date: Start date of leave in YYYY-MM-DD format
        end_date: End date of leave in YYYY-MM-DD format
        leave_type: Type of leave ('annual' or 'sick')
        reason: Optional reason for the leave application

    Returns:
        LeaveApplication: Details of the submitted leave application
    """
    cid = _new_cid()
    try:
        # Normalize and validate leave type
        normalized_type = leave_type.strip().lower()
        if normalized_type not in {"annual", "sick"}:
            raise Exception("Invalid leave_type: must be 'annual' or 'sick'")

        # Prepare request data
        leave_data = {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": normalized_type,
            "reason": reason,
        }

        url = f"{LEAVE_API_URL}/employees/{employee_id}/leave-requests"
        logger.info(f"[{cid}] apply_leave called for employee_id={employee_id}, url={url}")
        logger.debug(f"[{cid}] Payload: {_safe_json(leave_data)}")

        # Make API call
        t0 = time.monotonic()
        response = requests.post(url, json=leave_data, timeout=HTTP_TIMEOUT)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info(
            f"[{cid}] POST {url} -> {response.status_code} in {elapsed_ms}ms"
        )
        logger.debug(f"[{cid}] Response headers: {_safe_json(dict(response.headers), 1500)}")

        if response.status_code == 200:
            try:
                result = response.json()
            except ValueError:
                logger.error(f"[{cid}] Failed to parse JSON response: {response.text}")
                raise Exception("Invalid JSON in response from leave API")
            logger.debug(f"[{cid}] Parsed response: {_safe_json(result)}")
            return LeaveApplication(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                leave_type=cast(Literal["annual", "sick"], normalized_type),
                reason=reason,
                status=result.get("status", "submitted"),
                application_id=result.get("id", 0),
            )
        else:
            logger.error(
                f"[{cid}] Leave application failed: {response.status_code} - {_truncate(response.text)}"
            )
            raise Exception(f"Leave application failed: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"[{cid}] Network error applying for leave: {e}", exc_info=True)
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"[{cid}] Error applying for leave: {e}", exc_info=True)
        raise Exception(f"Error applying for leave: {str(e)}")

@mcp.tool()
def get_balance(employee_id: int) -> LeaveBalance:
    """
    Get leave balance for an employee (annual and sick only).

    Args:
        employee_id: The ID of the employee to check balance for

    Returns:
        LeaveBalance: Current annual and sick leave balances for the employee
    """
    cid = _new_cid()
    try:
        url = f"{LEAVE_API_URL}/employees/{employee_id}/balance"
        logger.info(f"[{cid}] get_balance called for employee_id={employee_id}, url={url}")

        # Make API call
        t0 = time.monotonic()
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info(f"[{cid}] GET {url} -> {response.status_code} in {elapsed_ms}ms")

        if response.status_code == 200:
            try:
                result = response.json()
            except ValueError:
                logger.error(f"[{cid}] Failed to parse JSON response: {response.text}")
                raise Exception("Invalid JSON in response from leave API")
            logger.debug(f"[{cid}] Parsed response: {_safe_json(result)}")
            annual = result.get("annual_balance", 0)
            sick = result.get("sick_balance", 0)
            return LeaveBalance(
                employee_id=employee_id,
                annual_balance=annual,
                sick_balance=sick,
            )
        else:
            logger.error(
                f"[{cid}] Balance check failed: {response.status_code} - {_truncate(response.text)}"
            )
            raise Exception(f"Balance check failed: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"[{cid}] Network error getting balance: {e}", exc_info=True)
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"[{cid}] Error getting balance: {e}", exc_info=True)
        raise Exception(f"Error getting balance: {str(e)}")

@mcp.resource("leave://employee/{employee_id}/applications")
def get_employee_applications(employee_id: str) -> str:
    """
    Get leave applications for a specific employee.

    Args:
        employee_id: Employee ID to get applications for

    Returns:
        JSON string containing the employee's leave applications
    """
    cid = _new_cid()
    url = f"{LEAVE_API_URL}/leave/{employee_id}/applications"
    try:
        logger.info(f"[{cid}] get_employee_applications called for employee_id={employee_id}, url={url}")
        t0 = time.monotonic()
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        logger.info(f"[{cid}] GET {url} -> {response.status_code} in {elapsed_ms}ms")

        if response.status_code == 200:
            body = _truncate(response.text, 2000)
            logger.debug(f"[{cid}] Applications response body: {body}")
            return response.text
        else:
            logger.error(f"[{cid}] Failed to get applications: {response.status_code} - {_truncate(response.text)}")
            return f'{{"error": "Failed to get applications for employee {employee_id}"}}'

    except Exception as e:
        logger.error(f"[{cid}] Error getting applications: {e}", exc_info=True)
        return f'{{"error": "Error getting applications: {str(e)}"}}'

@mcp.resource("leave://policies")
def get_leave_policies() -> str:
    """
    Get company leave policies and guidelines (annual and sick only).

    Returns:
        JSON string containing leave policies
    """
    logger.info("Retrieving leave policies")
    policies = {
        "annual_leave": {
            "description": "Annual vacation leave",
            "allocation": "20 days per year",
            "carryover": "Up to 5 days can be carried over to next year",
            "notice_period": "2 weeks advance notice required"
        },
        "sick_leave": {
            "description": "Medical leave for illness",
            "allocation": "10 days per year",
            "documentation": "Medical certificate required for leaves > 3 days",
            "notice_period": "As soon as possible"
        }
    }

    payload = json.dumps(policies, indent=2)
    logger.debug(f"Policies payload length: {len(payload)} bytes")
    return payload

@mcp.prompt()
def leave_application_template(employee_name: str, leave_type: Literal["annual", "sick"] = "annual") -> str:
    """
    Generate a leave application template.

    Args:
        employee_name: Name of the employee
        leave_type: Type of leave ('annual' or 'sick')

    Returns:
        A formatted leave application template
    """
    logger.info(f"Generating leave_application_template for employee_name={employee_name}, type={leave_type}")
    templates = {
        "annual": f"""
Dear Manager,

I would like to request annual leave for the following period:

Employee: {employee_name}
Leave Type: Annual Leave
Start Date: [YYYY-MM-DD]
End Date: [YYYY-MM-DD]
Reason: [Vacation/Personal time]

I have ensured that my current projects are up to date and have arranged for coverage of my responsibilities during my absence.

Please let me know if you need any additional information.

Best regards,
{employee_name}
        """,
        "sick": f"""
Dear Manager,

I need to request sick leave due to medical reasons:

Employee: {employee_name}
Leave Type: Sick Leave
Start Date: [YYYY-MM-DD]
End Date: [YYYY-MM-DD] (if known)
Reason: Medical/Health reasons

I will provide a medical certificate if the leave extends beyond 3 days as per company policy.

Thank you for your understanding.

Best regards,
{employee_name}
        """
    }

    key = str(leave_type).strip().lower()
    result = templates.get(key, templates["annual"])
    logger.debug(f"Template generated, length={len(result)} chars")
    return result

@mcp.prompt()
def leave_balance_inquiry() -> str:
    """
    Generate a prompt for checking leave balance.

    Returns:
        A template for leave balance inquiry
    """
    logger.info("Generating leave_balance_inquiry prompt")
    return """
To check your leave balance, I can help you retrieve your current leave allowances including:

- Annual leave days remaining
- Sick leave days available

Please provide your employee ID to check your current leave balance.

Example: "What is the leave balance for employee ID 123?"
    """

def main():
    """Main entry point for the MCP server."""
    port = int(os.getenv("PORT", 8000))
    env_name = os.getenv("AZURE_ENV_NAME") or os.getenv("ENVIRONMENT") or "local"

    logger.info(f"Starting Leave MCP Server v2 on port {port}")
    logger.info(f"Environment: {env_name}")
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info(f"HTTP timeout: {HTTP_TIMEOUT}s")
    logger.info(f"Leave API URL: {LEAVE_API_URL}")
    logger.info(f"Server name: {mcp.name}")
    # Default to streamable-http to prefer HTTP stream endpoints in web deployments
    transport_env = os.getenv("MCP_TRANSPORT", "streamable-http").strip().lower()
    transport: TransportType = "streamable-http"
    if transport_env == "stdio":
        transport = "stdio"
    elif transport_env == "streamable-http":
        transport = "streamable-http"
    elif transport_env == "sse":
        transport = "sse"
    else:
        logger.warning(f"Unknown MCP_TRANSPORT '{transport_env}', defaulting to 'streamable-http'")
        transport = "streamable-http"
    logger.info(f"MCP transport: {transport}")

    # Configure server settings
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port

    # Run the server with selected transport (SSE for Inspector, streamable-http for HTTP clients)
    mcp.run(transport=transport)

if __name__ == "__main__":
    main()
