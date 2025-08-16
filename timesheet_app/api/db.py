import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

PROVIDER = os.getenv("TIMESHEET_DB_PROVIDER", "auto").lower()

def _default_sqlite_url() -> str:
    appservice_data = Path("/home/site/data")
    docker_data = Path("/data")
    if appservice_data.exists():
        db_dir = appservice_data / "timesheet"
    else:
        db_dir = docker_data if docker_data.exists() else Path.cwd() / "data/timesheet"
    db_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(db_dir / 'timesheet.db').as_posix()}"

def _resolve_database_url() -> tuple[str, str]:
    raw = os.getenv("TIMESHEET_DATABASE_URL", "").strip()
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
    if not raw:
        raise RuntimeError("TIMESHEET_DATABASE_URL is required for MSSQL provider")
    return raw, "mssql"

DATABASE_URL, RESOLVED_PROVIDER = _resolve_database_url()

connect_args = {"check_same_thread": False} if RESOLVED_PROVIDER == "sqlite" else {}
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def should_seed() -> bool:
    return os.getenv("TIMESHEET_SEED_ON_START", "true").lower() in ("1", "true", "yes")

def provider() -> str:
    return RESOLVED_PROVIDER
