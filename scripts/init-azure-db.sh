#!/bin/bash
# Database initialization script for Azure deployment

set -e

echo "🗄️  Initializing databases..."

# Check if sqlcmd is available
if ! command -v sqlcmd &> /dev/null; then
    echo "📦 Installing SQL Server tools..."
    curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
    echo "deb [arch=amd64] https://packages.microsoft.com/ubuntu/20.04/prod focal main" | sudo tee /etc/apt/sources.list.d/mssql-release.list
    sudo apt-get update
    sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 unixodbc-dev
    export PATH="$PATH:/opt/mssql-tools18/bin"
fi

# Initialize Leave Database
echo "📅 Setting up Leave database..."
sqlcmd -C -S "${LEAVE_SQL_SERVER}.database.windows.net" \
        -d "${LEAVE_SQL_DB}" \
        -U "${LEAVE_SQL_ADMIN}" \
        -P "${LEAVE_SQL_PASSWORD}" \
        -i leave_app/sql/schema.sql

sqlcmd -C -S "${LEAVE_SQL_SERVER}.database.windows.net" \
        -d "${LEAVE_SQL_DB}" \
        -U "${LEAVE_SQL_ADMIN}" \
        -P "${LEAVE_SQL_PASSWORD}" \
        -i leave_app/sql/seed.sql

# Initialize Timesheet Database  
echo "⏰ Setting up Timesheet database..."
sqlcmd -C -S "${TIMESHEET_SQL_SERVER}.database.windows.net" \
        -d "${TIMESHEET_SQL_DB}" \
        -U "${TIMESHEET_SQL_ADMIN}" \
        -P "${TIMESHEET_SQL_PASSWORD}" \
        -i timesheet_app/sql/schema.sql

sqlcmd -C -S "${TIMESHEET_SQL_SERVER}.database.windows.net" \
        -d "${TIMESHEET_SQL_DB}" \
        -U "${TIMESHEET_SQL_ADMIN}" \
        -P "${TIMESHEET_SQL_PASSWORD}" \
        -i timesheet_app/sql/seed.sql

echo "✅ Database initialization complete!"
echo "🎯 Ready to deploy MCP services!"
