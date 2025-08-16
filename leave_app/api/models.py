from datetime import date
from sqlalchemy import Date, ForeignKey, String, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    balance: Mapped["LeaveBalance"] = relationship("LeaveBalance", back_populates="employee", uselist=False)
    requests: Mapped[list["LeaveRequest"]] = relationship("LeaveRequest", back_populates="employee")

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True, nullable=False)
    annual_balance: Mapped[int] = mapped_column(Integer, default=20)
    sick_balance: Mapped[int] = mapped_column(Integer, default=10)

    employee: Mapped[Employee] = relationship("Employee", back_populates="balance")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[str] = mapped_column(String, nullable=False)  # 'annual' | 'sick'
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # 'pending' | 'approved' | 'rejected'

    employee: Mapped[Employee] = relationship("Employee", back_populates="requests")
