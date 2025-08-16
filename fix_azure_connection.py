#!/usr/bin/env python3
"""
Azure SQL Connection String Fixer for Leave API
This script helps diagnose and fix connection string issues in Azure App Service
"""

import os
import re
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_connection_string(url):
    """Analyze the connection string for potential conflicts"""
    logger.info(f"Analyzing connection string...")
    
    if not url:
        logger.error("No connection string provided")
        return None
    
    # Parse the URL
    if "?" not in url:
        logger.info("No query parameters found in connection string")
        return url
    
    base_url, query_string = url.split("?", 1)
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Query parameters: {query_string}")
    
    # Parse parameters
    params = {}
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key.lower()] = (key, value)  # Store original case key
    
    logger.info("Found parameters:")
    for key, (orig_key, value) in params.items():
        logger.info(f"  {orig_key} = {value}")
    
    # Check for conflicts
    auth_present = any("authentication" in key for key in params.keys())
    integrated_present = any("integrated" in key for key in params.keys())
    trusted_present = any("trusted" in key for key in params.keys())
    
    logger.info(f"Authentication parameter present: {auth_present}")
    logger.info(f"Integrated Security parameter present: {integrated_present}")
    logger.info(f"Trusted Connection parameter present: {trusted_present}")
    
    if auth_present and (integrated_present or trusted_present):
        logger.warning("CONFLICT DETECTED: Authentication and Integrated Security/Trusted Connection cannot be used together")
        return fix_connection_string(url)
    
    logger.info("No conflicts detected in connection string")
    return url

def fix_connection_string(url):
    """Fix connection string by removing conflicting parameters"""
    logger.info("Fixing connection string conflicts...")
    
    if "?" not in url:
        return url
    
    base_url, query_string = url.split("?", 1)
    
    # Parse and filter parameters
    new_params = []
    removed_params = []
    
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            key_lower = key.lower()
            
            # Check if this is a conflicting parameter
            if ("integrated" in key_lower or "trusted" in key_lower) and "authentication=" in query_string.lower():
                removed_params.append(param)
                logger.info(f"Removing conflicting parameter: {param}")
            else:
                new_params.append(param)
    
    # Add explicit Trusted_Connection=no if Authentication is present
    has_auth = any("authentication=" in p.lower() for p in new_params)
    has_trusted = any("trusted_connection=" in p.lower() for p in new_params)
    
    if has_auth and not has_trusted:
        new_params.append("Trusted_Connection=no")
        logger.info("Added explicit Trusted_Connection=no")
    
    # Reconstruct URL
    if new_params:
        fixed_url = f"{base_url}?{'&'.join(new_params)}"
    else:
        fixed_url = base_url
    
    logger.info(f"Removed {len(removed_params)} conflicting parameters")
    logger.info(f"Fixed connection string created")
    
    return fixed_url

def test_connection(url):
    """Test the database connection"""
    try:
        from sqlalchemy import create_engine, text
        
        logger.info("Testing database connection...")
        engine = create_engine(url, pool_pre_ping=True, echo=False)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            logger.info(f"Connection successful! Test query result: {row[0]}")
            return True
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("Azure SQL Connection String Fixer")
    logger.info("=" * 50)
    
    # Get connection string from environment
    connection_string = os.getenv("LEAVE_DATABASE_URL")
    
    if not connection_string:
        logger.error("LEAVE_DATABASE_URL environment variable not found")
        logger.info("Please set the LEAVE_DATABASE_URL environment variable")
        return 1
    
    # Hide password in logs
    safe_url = connection_string
    if ":" in safe_url and "@" in safe_url:
        parts = safe_url.split("://", 1)
        if len(parts) == 2:
            scheme, rest = parts
            if "@" in rest:
                creds, server_part = rest.split("@", 1)
                if ":" in creds:
                    user, _ = creds.split(":", 1)
                    safe_url = f"{scheme}://{user}:***@{server_part}"
    
    logger.info(f"Original connection string: {safe_url}")
    
    # Analyze and fix
    fixed_url = analyze_connection_string(connection_string)
    
    if fixed_url != connection_string:
        logger.info("Connection string was modified")
        
        # Test the fixed connection
        if test_connection(fixed_url):
            logger.info("✅ Fixed connection string works!")
            logger.info("Recommended action: Update your Azure App Service settings with the fixed connection string")
        else:
            logger.error("❌ Fixed connection string still doesn't work")
    else:
        logger.info("Connection string was not modified")
        
        # Test the original connection
        if test_connection(connection_string):
            logger.info("✅ Original connection string works!")
        else:
            logger.error("❌ Original connection string doesn't work")
    
    return 0

if __name__ == "__main__":
    exit(main())
