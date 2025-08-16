from datetime import date
from typing import List, Optional

import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import Base, SessionLocal, engine, get_db, should_seed, provider
from . import models, schemas

Base.metadata.create_all(bind=engine)

# Idempotent seed for SQLite or empty DBs
if should_seed():
    from sqlalchemy import select
    try:
        with engine.begin() as conn:
            # Check employees count
            count = conn.execute(select(models.Employee).limit(1)).first()
            if not count:
                # Minimal starter data
                with SessionLocal() as db:
                    alice = models.Employee(name="Alice Johnson", email="alice@example.com")
                    bob = models.Employee(name="Bob Smith", email="bob@example.com")
                    db.add_all([alice, bob])
                    db.flush()
                    db.add_all([
                        models.LeaveBalance(employee_id=alice.id, annual_balance=20, sick_balance=10),
                        models.LeaveBalance(employee_id=bob.id, annual_balance=18, sick_balance=9),
                    ])
                    db.commit()
    except Exception as _:
        # Don't block app start on seed issues
        pass

app = FastAPI(title="Leave Application API")


@app.get("/health")
def health():
    return {"status": "ok"}


# Employees
@app.post("/employees", response_model=schemas.Employee)
def create_employee(emp: schemas.EmployeeCreate, db=Depends(get_db)):
    existing = db.query(models.Employee).filter(models.Employee.email == emp.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this email already exists")
    obj = models.Employee(name=emp.name, email=emp.email)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # initialize balance
    bal = models.LeaveBalance(employee_id=obj.id, annual_balance=emp.annual_balance or 20, sick_balance=emp.sick_balance or 10)
    db.add(bal)
    db.commit()
    return obj


@app.get("/employees", response_model=List[schemas.Employee])
def list_employees(db=Depends(get_db)):
    return db.query(models.Employee).all()


@app.get("/employees/{employee_id}", response_model=schemas.Employee)
def get_employee(employee_id: int, db=Depends(get_db)):
    obj = db.query(models.Employee).get(employee_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Employee not found")
    return obj


# Leave balance
@app.get("/employees/{employee_id}/balance", response_model=schemas.LeaveBalance)
def get_balance(employee_id: int, db=Depends(get_db)):
    bal = (
        db.query(models.LeaveBalance)
        .filter(models.LeaveBalance.employee_id == employee_id)
        .first()
    )
    if not bal:
        raise HTTPException(status_code=404, detail="Balance not found")
    return bal


@app.post("/employees/{employee_id}/balance", response_model=schemas.LeaveBalance)
def set_balance(employee_id: int, data: schemas.LeaveBalanceUpdate, db=Depends(get_db)):
    bal = (
        db.query(models.LeaveBalance)
        .filter(models.LeaveBalance.employee_id == employee_id)
        .first()
    )
    if not bal:
        bal = models.LeaveBalance(employee_id=employee_id, annual_balance=0, sick_balance=0)
        db.add(bal)
        db.flush()
    if data.annual_balance is not None:
        bal.annual_balance = data.annual_balance
    if data.sick_balance is not None:
        bal.sick_balance = data.sick_balance
    db.commit()
    db.refresh(bal)
    return bal


# Leave requests
@app.post("/employees/{employee_id}/leave-requests", response_model=schemas.LeaveRequest)
def create_leave_request(employee_id: int, req: schemas.LeaveRequestCreate, db=Depends(get_db)):
    emp = db.query(models.Employee).get(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    # simple balance check for annual leave type
    days = (req.end_date - req.start_date).days + 1
    bal = (
        db.query(models.LeaveBalance)
        .filter(models.LeaveBalance.employee_id == employee_id)
        .first()
    )
    if not bal:
        raise HTTPException(status_code=400, detail="Balance not initialized")
    if req.leave_type.lower() == "annual" and bal.annual_balance < days:
        raise HTTPException(status_code=400, detail="Insufficient annual leave balance")
    if req.leave_type.lower() == "sick" and bal.sick_balance < days:
        raise HTTPException(status_code=400, detail="Insufficient sick leave balance")

    obj = models.LeaveRequest(
        employee_id=employee_id,
        start_date=req.start_date,
        end_date=req.end_date,
        leave_type=req.leave_type,
        reason=req.reason,
        status="pending",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.get("/employees/{employee_id}/leave-requests", response_model=List[schemas.LeaveRequest])
def list_leave_requests(employee_id: int, db=Depends(get_db)):
    return (
        db.query(models.LeaveRequest)
        .filter(models.LeaveRequest.employee_id == employee_id)
        .order_by(models.LeaveRequest.start_date.desc())
        .all()
    )


@app.post("/leave-requests/{request_id}/status", response_model=schemas.LeaveRequest)
def update_leave_status(request_id: int, data: schemas.LeaveStatusUpdate, db=Depends(get_db)):
    obj = db.query(models.LeaveRequest).get(request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if data.status not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    # adjust balance if moving to approved from non-approved or vice-versa
    days = (obj.end_date - obj.start_date).days + 1
    bal = (
        db.query(models.LeaveBalance)
        .filter(models.LeaveBalance.employee_id == obj.employee_id)
        .first()
    )
    if not bal:
        raise HTTPException(status_code=400, detail="Balance not initialized")
    prev = obj.status
    new = data.status
    if prev != "approved" and new == "approved":
        if obj.leave_type.lower() == "annual":
            if bal.annual_balance < days:
                raise HTTPException(status_code=400, detail="Insufficient annual balance for approval")
            bal.annual_balance -= days
        elif obj.leave_type.lower() == "sick":
            if bal.sick_balance < days:
                raise HTTPException(status_code=400, detail="Insufficient sick balance for approval")
            bal.sick_balance -= days
    elif prev == "approved" and new != "approved":
        if obj.leave_type.lower() == "annual":
            bal.annual_balance += days
        elif obj.leave_type.lower() == "sick":
            bal.sick_balance += days
    obj.status = new
    db.commit()
    db.refresh(obj)
    return obj


# Serve simple web UI (mount at the end so it doesn't interfere with API routes)
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")

 
