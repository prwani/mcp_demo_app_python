#!/bin/bash
# Fix Azure App Settings for URL Encoding
# Run this script to update the connection strings with proper URL encoding

# Set your Azure resource variables (update these to match your deployment)
export RG="mcp-python-demo-rg-7859"           # e.g., "mcp-python-demo-rg-1234"
export LEAVE_API_APP="mcp-leave-api-7859"      # e.g., "mcp-leave-api-1234"
export TIMESHEET_API_APP="mcp-timesheet-api-7859"  # e.g., "mcp-timesheet-api-1234"

# SQL Server details
export LEAVE_SQL_SERVER="leave-sql-server-7859"      # Your actual server name
export LEAVE_SQL_DB="leave_db"
export LEAVE_SQL_ADMIN="sqladminuser"
export LEAVE_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"

export TIMESHEET_SQL_SERVER="timesheet-sql-server-7859"  # Your actual server name
export TIMESHEET_SQL_DB="timesheet_db"
export TIMESHEET_SQL_ADMIN="sqladminuser"
export TIMESHEET_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"

# Function to URL-encode password
url_encode_password() {
    python3 -c "from urllib.parse import quote_plus; print(quote_plus('$1'))"
}

# Generate properly encoded connection strings
ENCODED_LEAVE_PASSWORD=$(url_encode_password "$LEAVE_SQL_PASSWORD")
ENCODED_TIMESHEET_PASSWORD=$(url_encode_password "$TIMESHEET_SQL_PASSWORD")

LEAVE_DATABASE_URL="mssql+pyodbc://${LEAVE_SQL_ADMIN}:${ENCODED_LEAVE_PASSWORD}@${LEAVE_SQL_SERVER}.database.windows.net:1433/${LEAVE_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"

TIMESHEET_DATABASE_URL="mssql+pyodbc://${TIMESHEET_SQL_ADMIN}:${ENCODED_TIMESHEET_PASSWORD}@${TIMESHEET_SQL_SERVER}.database.windows.net:1433/${TIMESHEET_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"

echo "🔧 Updating Azure App Settings with URL-encoded connection strings..."

# Update Leave API settings
echo "📅 Updating Leave API settings..."
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
    LEAVE_DATABASE_URL="$LEAVE_DATABASE_URL"

if [ $? -eq 0 ]; then
    echo "✅ Leave API settings updated successfully"
else
    echo "❌ Failed to update Leave API settings"
fi

# Update Timesheet API settings
echo "⏰ Updating Timesheet API settings..."
az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
    TIMESHEET_DATABASE_URL="$TIMESHEET_DATABASE_URL"

if [ $? -eq 0 ]; then
    echo "✅ Timesheet API settings updated successfully"
else
    echo "❌ Failed to update Timesheet API settings"
fi

echo ""
echo "🎯 Configuration update complete!"
echo ""
echo "📝 Updated connection strings (passwords hidden):"
echo "Leave API:     ${LEAVE_DATABASE_URL//${ENCODED_LEAVE_PASSWORD}/***}"
echo "Timesheet API: ${TIMESHEET_DATABASE_URL//${ENCODED_TIMESHEET_PASSWORD}/***}"
echo ""
echo "🔄 The web apps will automatically restart with the new settings."
echo "⏳ Allow 1-2 minutes for the apps to restart and pick up the new configuration."
