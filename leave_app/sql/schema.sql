-- Azure SQL DDL for Leave Application

CREATE TABLE dbo.employees (
  id INT IDENTITY(1,1) PRIMARY KEY,
  name NVARCHAR(200) NOT NULL,
  email NVARCHAR(200) NOT NULL UNIQUE
);
GO

CREATE TABLE dbo.leave_balances (
  id INT IDENTITY(1,1) PRIMARY KEY,
  employee_id INT NOT NULL,
  annual_balance INT NOT NULL DEFAULT 20,
  sick_balance INT NOT NULL DEFAULT 10,
  CONSTRAINT FK_leave_balances_employee FOREIGN KEY (employee_id) REFERENCES dbo.employees(id)
);
GO

CREATE TABLE dbo.leave_requests (
  id INT IDENTITY(1,1) PRIMARY KEY,
  employee_id INT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  leave_type NVARCHAR(50) NOT NULL,
  reason NVARCHAR(1000) NULL,
  status NVARCHAR(50) NOT NULL DEFAULT 'pending',
  CONSTRAINT FK_leave_requests_employee FOREIGN KEY (employee_id) REFERENCES dbo.employees(id)
);
GO

CREATE INDEX IX_leave_requests_employee ON dbo.leave_requests(employee_id);
GO

CREATE INDEX IX_leave_balances_employee ON dbo.leave_balances(employee_id);
GO
