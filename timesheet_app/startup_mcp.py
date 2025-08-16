#!/usr/bin/env python3
"""
Entry point for Azure App Service deployment (non-Docker) for Timesheet MCP Server.
Reference this in the Azure Web App startup command.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure App Service deployment root is on sys.path
APP_ROOT = os.environ.get("APP_HOME", "/home/site/wwwroot")
if os.path.isdir(APP_ROOT) and APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

logger.info("Starting Timesheet MCP Server application...")

if __name__ == "__main__":
    import uvicorn
    try:
        try:
            from mcp_server.server import app  # type: ignore
        except Exception:
            from timesheet_app.mcp_server.server import app
        port = int(os.environ.get("PORT", 8012))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error("Failed to start application: %s\nSYSPATH=%s", e, sys.path)
        raise
