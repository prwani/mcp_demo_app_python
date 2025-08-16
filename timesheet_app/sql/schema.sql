-- Azure SQL DDL for Timesheet Application
CREATE TABLE dbo.employees (
  id INT IDENTITY(1,1) PRIMARY KEY,
  name NVARCHAR(200) NOT NULL,
  email NVARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE dbo.timesheet_entries (
  id INT IDENTITY(1,1) PRIMARY KEY,
  employee_id INT NOT NULL,
  entry_date DATE NOT NULL,
  hours INT NOT NULL,
  project NVARCHAR(200) NULL,
  notes NVARCHAR(1000) NULL,
  CONSTRAINT FK_timesheet_entries_employee FOREIGN KEY (employee_id) REFERENCES dbo.employees(id)
);

CREATE INDEX IX_timesheet_employee ON dbo.timesheet_entries(employee_id);
CREATE INDEX IX_timesheet_date ON dbo.timesheet_entries(entry_date);
