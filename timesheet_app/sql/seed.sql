-- Seed data for Timesheet Application (10+ employees and entries)
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

INSERT INTO dbo.timesheet_entries (employee_id, entry_date, hours, project, notes) VALUES
 (1, '2025-08-11', 8, 'Alpha', 'Dev work'),
 (2, '2025-08-11', 8, 'Beta', 'API fixes'),
 (3, '2025-08-11', 6, 'Gamma', 'Docs'),
 (4, '2025-08-11', 9, 'Alpha', 'Overtime'),
 (5, '2025-08-11', 8, 'Ops', 'Support'),
 (6, '2025-08-11', 7, 'Ops', 'On-call'),
 (7, '2025-08-11', 8, 'Delta', 'Testing'),
 (8, '2025-08-11', 8, 'Epsilon', 'Feature work'),
 (9, '2025-08-11', 5, 'Alpha', 'Meetings'),
 (10,'2025-08-11', 8, 'Beta', 'Bugfixing'),
 (11,'2025-08-11', 8, 'Ops', 'Infra');
