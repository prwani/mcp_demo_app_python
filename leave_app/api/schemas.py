from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class EmployeeBase(BaseModel):
    name: str
    email: str

class EmployeeCreate(EmployeeBase):
    annual_balance: Optional[int] = Field(default=20)
    sick_balance: Optional[int] = Field(default=10)

class Employee(EmployeeBase):
    id: int
    class Config:
        from_attributes = True

class LeaveBalance(BaseModel):
    id: int
    employee_id: int
    annual_balance: int
    sick_balance: int
    class Config:
        from_attributes = True

class LeaveBalanceUpdate(BaseModel):
    annual_balance: Optional[int] = None
    sick_balance: Optional[int] = None

class LeaveRequestBase(BaseModel):
    start_date: date
    end_date: date
    leave_type: str
    reason: Optional[str] = None

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequest(LeaveRequestBase):
    id: int
    employee_id: int
    status: str
    class Config:
        from_attributes = True

class LeaveStatusUpdate(BaseModel):
    status: str
