-- Seed data for Leave Application (10+ employees, balances, and sample requests)
SET IDENTITY_INSERT dbo.employees ON;
INSERT INTO dbo.employees (id, name, email) VALUES
 (1,'Alice Johnson','alice@example.com'),
 (2,'Bob Smith','bob@example.com'),
 (3,'Carol Lee','carol@example.com'),
 (4,'Dan Brown','dan@example.com'),
 (5,'Eva Green','eva@example.com'),
 (6,'Frank Moore','frank@example.com'),
 (7,'Grace Kim','grace@example.com'),
 (8,'Hank Li','hank@example.com'),
 (9,'Ivy Chen','ivy@example.com'),
 (10,'Jack Wu','jack@example.com'),
 (11,'Kim Patel','kim@example.com');
SET IDENTITY_INSERT dbo.employees OFF;

INSERT INTO dbo.leave_balances (employee_id, annual_balance, sick_balance) VALUES
 (1, 20, 10), (2, 18, 9), (3, 15, 8), (4, 22, 12), (5, 25, 10),
 (6, 12, 6), (7, 20, 10), (8, 17, 9), (9, 14, 7), (10, 19, 9), (11, 20, 10);

INSERT INTO dbo.leave_requests (employee_id, start_date, end_date, leave_type, reason, status) VALUES
 (1, '2025-08-20','2025-08-22','annual','Family trip','approved'),
 (2, '2025-08-25','2025-08-25','sick','Flu','pending'),
 (3, '2025-09-01','2025-09-03','annual','Conference','rejected'),
 (4, '2025-09-10','2025-09-12','annual','Vacation','pending'),
 (5, '2025-09-15','2025-09-16','sick','Doctor appointment','approved'),
 (6, '2025-09-18','2025-09-19','annual','Wedding','pending'),
 (7, '2025-10-01','2025-10-05','annual','Travel','pending'),
 (8, '2025-10-08','2025-10-08','sick','Cold','approved'),
 (9, '2025-10-12','2025-10-13','annual','Family event','pending'),
 (10,'2025-10-20','2025-10-22','annual','Holidays','pending');
