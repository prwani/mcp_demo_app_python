#!/usr/bin/env python3
"""
Simple startup for Azure App Service
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, '/home/site/wwwroot')

logger.info("Starting Leave API...")

try:
    from leave_app.api.main import app
    logger.info("✅ Successfully imported app")
    
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting on port {port}")
    
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=port)
    
except Exception as e:
    logger.error(f"❌ Failed to start: {e}")
    import traceback
    traceback.print_exc()
    raise
