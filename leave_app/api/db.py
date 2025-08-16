import os
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Provider selection: sqlite (default) or mssql
PROVIDER = os.getenv("LEAVE_DB_PROVIDER", "auto").lower()

def _default_sqlite_url() -> str:
    """Decide a durable SQLite location for Azure App Service or Docker/local."""
    # Prefer App Service persistent storage if available
    appservice_data = Path("/home/site/data")
    docker_data = Path("/data")
    if appservice_data.exists():
        db_dir = appservice_data / "leave"
    else:
        db_dir = docker_data if docker_data.exists() else Path.cwd() / "data/leave"
    db_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(db_dir / 'leave.db').as_posix()}"

def _resolve_database_url() -> tuple[str, str]:
    """
    Resolve final SQLAlchemy connection URL and provider label.
    Returns (url, provider) where provider in {"sqlite","mssql"}.
    """
    raw = os.getenv("LEAVE_DATABASE_URL", "").strip()
    prov = PROVIDER
    if prov == "auto":
        if raw.startswith("sqlite:"):
            prov = "sqlite"
        elif raw:
            prov = "mssql"
        else:
            prov = "sqlite"
    if prov == "sqlite":
        if not raw or not raw.startswith("sqlite:"):
            raw = _default_sqlite_url()
        return raw, "sqlite"
    # mssql branch
    if not raw:
        raise RuntimeError("LEAVE_DATABASE_URL is required for MSSQL provider")
    return raw, "mssql"

DATABASE_URL, RESOLVED_PROVIDER = _resolve_database_url()

# Managed Identity (MSI) toggle for Entra auth with Azure SQL (only used for mssql)
USE_MANAGED_IDENTITY = os.getenv("LEAVE_USE_MANAGED_IDENTITY", "false").lower() in ("1", "true", "yes")

def _strip_conflicting_params(url: str) -> str:
    """Remove Integrated Security / Trusted_Connection from URL query string (case-insensitive)."""
    if not url or "?" not in url:
        return url
    base, query = url.split("?", 1)
    parts = []
    for p in query.split("&"):
        pl = p.lower()
        # More comprehensive parameter stripping for Entra authentication
        if (pl.startswith("trusted_connection=") or 
            pl.startswith("integrated security=") or
            pl.startswith("integrated%20security=") or  # URL encoded version
            pl.startswith("integratedsecurity=") or     # No space version
            pl.startswith("trustedconnection=") or      # No underscore version
            "integrated" in pl.split("=")[0] or         # Parameter name contains integrated
            "trusted" in pl.split("=")[0]):             # Parameter name contains trusted
            # drop conflicting params for Entra auth
            logger.info(f"Removing conflicting parameter for Entra auth: {p}")
            continue
        parts.append(p)
    return base + ("?" + "&".join(parts) if parts else "")

# For Entra-only databases, always use managed identity authentication
# Remove username/password from connection string and use ActiveDirectoryMsi
if RESOLVED_PROVIDER == "mssql" and USE_MANAGED_IDENTITY:
    # Parse the connection string to remove username/password and add managed identity auth
    if "://" in DATABASE_URL:
        scheme, rest = DATABASE_URL.split("://", 1)
        if "@" in rest:
            # Remove username:password@ part
            _, server_part = rest.split("@", 1)
            DATABASE_URL = f"{scheme}://@{server_part}"
        
        # Ensure Authentication=ActiveDirectoryMsi is present
        if "authentication=" not in DATABASE_URL.lower():
            sep = "&" if "?" in DATABASE_URL else "?"
            DATABASE_URL = f"{DATABASE_URL}{sep}Authentication=ActiveDirectoryMsi"
        
        logger.info("Using managed identity authentication for Entra-only database")

if RESOLVED_PROVIDER == "mssql":
    # Always strip conflicting params that may be present from App Settings
    DATABASE_URL = _strip_conflicting_params(DATABASE_URL)

# Log the connection attempt (without password)
safe_url = DATABASE_URL
if ":" in safe_url and "@" in safe_url:
    # Hide password in logs
    parts = safe_url.split("://", 1)
    if len(parts) == 2:
        scheme, rest = parts
        if "@" in rest:
            creds, server_part = rest.split("@", 1)
            if ":" in creds:
                user, _ = creds.split(":", 1)
                safe_url = f"{scheme}://{user}:***@{server_part}"

logger.info(f"[leave] Provider={RESOLVED_PROVIDER} | URL={safe_url}")

# If Authentication is present, explicitly prevent conflicts
if RESOLVED_PROVIDER == "mssql" and "authentication=" in DATABASE_URL.lower():
    # Remove any remaining conflicting parameters and add explicit ones
    url_parts = DATABASE_URL.split("?")
    if len(url_parts) == 2:
        base_url, params = url_parts
        param_dict = {}
        
        # Parse existing parameters
        for param in params.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                param_dict[key.lower()] = value
        
        # Remove any conflicting parameters
        conflicting_keys = [k for k in param_dict.keys() 
                          if "trusted" in k or "integrated" in k]
        for key in conflicting_keys:
            del param_dict[key]
            logger.info(f"Removed conflicting parameter: {key}")
        
        # Add explicit parameters to prevent driver from adding them
        param_dict["trusted_connection"] = "no"
        
        # Reconstruct URL
        new_params = "&".join([f"{k}={v}" for k, v in param_dict.items()])
        DATABASE_URL = f"{base_url}?{new_params}"
        logger.info("Reconstructed connection string with explicit parameters")

# Final check - log all parameters to debug
if "?" in DATABASE_URL:
    params = DATABASE_URL.split("?", 1)[1]
    logger.info(f"Final connection parameters: {params}")

try:
    connect_args: dict = {"timeout": 30} if RESOLVED_PROVIDER == "mssql" else {}
    if RESOLVED_PROVIDER == "sqlite":
        # Needed for FastAPI + SQLite in threaded server
        connect_args.update({"check_same_thread": False})
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL query logging
        connect_args=connect_args
    )
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connection successful!")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    logger.error(f"Connection string pattern: {safe_url}")
    
    # Additional diagnostic information
    error_str = str(e).lower()
    if "fa001" in error_str or "authentication option" in error_str:
        logger.error("ERROR DIAGNOSIS: Authentication conflict detected!")
        logger.error("The connection string contains conflicting authentication parameters.")
        logger.error("For Entra-only databases, use managed identity authentication.")
        logger.error("SOLUTION: Use Authentication=ActiveDirectoryMsi and remove username/password.")
    elif "login failed" in error_str or "cannot open database" in error_str:
        logger.error("ERROR DIAGNOSIS: Authentication failed!")
        logger.error("This appears to be an Entra-only database.")
        logger.error("SOLUTION: Ensure managed identity is enabled and configured as Azure AD admin.")
        logger.error("Run: ./setup_entra_auth.sh to configure properly.")
    elif "timeout" in error_str:
        logger.error("ERROR DIAGNOSIS: Connection timeout!")
        logger.error("SOLUTION: Check network connectivity and firewall rules.")
    
    if RESOLVED_PROVIDER == "mssql":
        logger.error("For Entra authentication setup, run: ./setup_entra_auth.sh")
    
    raise e  # Re-raise the original error
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional bootstrap helpers (used by main.py)
def should_seed() -> bool:
    return os.getenv("LEAVE_SEED_ON_START", "true").lower() in ("1", "true", "yes")

def provider() -> str:
    return RESOLVED_PROVIDER

