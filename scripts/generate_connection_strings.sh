#!/bin/bash
"""
Helper script to generate properly URL-encoded Azure SQL connection strings.
Usage: source this script after setting your Azure SQL variables.
"""

# Function to URL-encode a password
url_encode_password() {
    python3 -c "from urllib.parse import quote_plus; print(quote_plus('$1'))"
}

# Generate URL-encoded connection strings if the variables are set
if [[ -n "$LEAVE_SQL_ADMIN" && -n "$LEAVE_SQL_PASSWORD" && -n "$LEAVE_SQL_SERVER" && -n "$LEAVE_SQL_DB" ]]; then
    ENCODED_LEAVE_PASSWORD=$(url_encode_password "$LEAVE_SQL_PASSWORD")
    export LEAVE_DATABASE_URL="mssql+pyodbc://${LEAVE_SQL_ADMIN}:${ENCODED_LEAVE_PASSWORD}@${LEAVE_SQL_SERVER}.database.windows.net:1433/${LEAVE_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
    echo "✅ Generated LEAVE_DATABASE_URL with URL-encoded password"
fi

if [[ -n "$TIMESHEET_SQL_ADMIN" && -n "$TIMESHEET_SQL_PASSWORD" && -n "$TIMESHEET_SQL_SERVER" && -n "$TIMESHEET_SQL_DB" ]]; then
    ENCODED_TIMESHEET_PASSWORD=$(url_encode_password "$TIMESHEET_SQL_PASSWORD")
    export TIMESHEET_DATABASE_URL="mssql+pyodbc://${TIMESHEET_SQL_ADMIN}:${ENCODED_TIMESHEET_PASSWORD}@${TIMESHEET_SQL_SERVER}.database.windows.net:1433/${TIMESHEET_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
    echo "✅ Generated TIMESHEET_DATABASE_URL with URL-encoded password"
fi

# Display the generated URLs (without showing the actual password)
if [[ -n "$LEAVE_DATABASE_URL" ]]; then
    echo "LEAVE_DATABASE_URL: ${LEAVE_DATABASE_URL//${ENCODED_LEAVE_PASSWORD}/***}"
fi

if [[ -n "$TIMESHEET_DATABASE_URL" ]]; then
    echo "TIMESHEET_DATABASE_URL: ${TIMESHEET_DATABASE_URL//${ENCODED_TIMESHEET_PASSWORD}/***}"
fi
