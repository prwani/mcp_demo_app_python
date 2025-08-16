#!/usr/bin/env python3
"""
Entry point for Azure App Service deployment (non-Docker)
This file should be referenced in the Azure App Service startup command.
"""

import os
import sys
import logging

# Configure logging for Azure App Service
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path so we can import from leave_app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger.info("Starting Leave API application...")

if __name__ == "__main__":
    import uvicorn
    
    try:
        # Import the app to test database connection early
        from leave_app.api.main import app
        logger.info("Successfully imported FastAPI app")
        
        # Get port from environment (Azure sets this)
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Starting server on port {port}")
        
        # Run the app
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
