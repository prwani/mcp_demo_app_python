from datetime import date
from typing import Optional
from pydantic import BaseModel

class EmployeeBase(BaseModel):
    name: str
    email: str

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    class Config:
        from_attributes = True

class TimesheetEntryBase(BaseModel):
    entry_date: date
    hours: int
    project: Optional[str] = None
    notes: Optional[str] = None

class TimesheetEntryCreate(TimesheetEntryBase):
    pass

class TimesheetEntry(TimesheetEntryBase):
    id: int
    employee_id: int
    class Config:
        from_attributes = True
