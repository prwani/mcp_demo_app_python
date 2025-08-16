import os
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .db import Base, engine, get_db, should_seed, SessionLocal
from . import models, schemas

Base.metadata.create_all(bind=engine)

if should_seed():
    from sqlalchemy import select
    try:
        from sqlalchemy import select
        with engine.connect() as conn:
            exists = conn.execute(select(models.Employee).limit(1)).first()
        if not exists:
            from datetime import date
            with SessionLocal() as db:
                e1 = models.Employee(name="Alice Johnson", email="alice@example.com")
                e2 = models.Employee(name="Bob Smith", email="bob@example.com")
                db.add_all([e1, e2])
                db.flush()
                db.add_all([
                    models.TimesheetEntry(employee_id=e1.id, entry_date=date.today(), hours=8, project="PROJ001", notes="Init"),
                    models.TimesheetEntry(employee_id=e2.id, entry_date=date.today(), hours=7, project="OPS", notes="Init"),
                ])
                db.commit()
    except Exception:
        pass

app = FastAPI(title="Timesheet Application API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/employees", response_model=schemas.Employee)
def create_employee(emp: schemas.EmployeeCreate, db=Depends(get_db)):
    existing = db.query(models.Employee).filter(models.Employee.email == emp.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    obj = models.Employee(name=emp.name, email=emp.email)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/employees", response_model=List[schemas.Employee])
def list_employees(db=Depends(get_db)):
    return db.query(models.Employee).all()

@app.post("/employees/{employee_id}/entries", response_model=schemas.TimesheetEntry)
def create_entry(employee_id: int, item: schemas.TimesheetEntryCreate, db=Depends(get_db)):
    emp = db.query(models.Employee).get(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    obj = models.TimesheetEntry(
        employee_id=employee_id,
        entry_date=item.entry_date,
        hours=item.hours,
        project=item.project,
        notes=item.notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/employees/{employee_id}/entries", response_model=List[schemas.TimesheetEntry])
def list_entries(employee_id: int, db=Depends(get_db)):
    return (
        db.query(models.TimesheetEntry)
        .filter(models.TimesheetEntry.employee_id == employee_id)
        .order_by(models.TimesheetEntry.entry_date.desc())
        .all()
    )

# Serve simple web UI
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
