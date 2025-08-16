#!/bin/bash

# Fix Azure SQL Connection String for Leave API
# This script updates the Azure App Service with a properly formatted connection string

set -e

# Configuration - Update these values to match your deployment
RESOURCE_GROUP="mcp-python-demo-rg-7859"
APP_NAME="mcp-leave-api-7859"
SQL_SERVER="leave-sql-server-7859"
DATABASE="leave_db"
SQL_ADMIN="sqladminuser"

echo "🔧 Fixing Azure SQL Connection String for Leave API..."
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "SQL Server: $SQL_SERVER"
echo "Database: $DATABASE"

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI first."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo ""
echo "Please enter the SQL admin password for user '$SQL_ADMIN':"
read -s SQL_PASSWORD

if [ -z "$SQL_PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

echo ""
echo "🔗 Creating clean connection string..."

# URL encode the password
ENCODED_PASSWORD=$(python3 -c "
import urllib.parse
password = '$SQL_PASSWORD'
encoded = urllib.parse.quote_plus(password)
print(encoded)
")

# Create a clean connection string without conflicting parameters
CONNECTION_STRING="mssql+pyodbc://${SQL_ADMIN}:${ENCODED_PASSWORD}@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Trusted_Connection=no"

echo "✅ Connection string created"

echo ""
echo "🚀 Updating Azure App Service settings..."

# Update the app settings
az webapp config appsettings set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings LEAVE_DATABASE_URL="$CONNECTION_STRING" \
    --output table

echo ""
echo "🔄 Restarting the web app to apply changes..."
az webapp restart \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP"

echo ""
echo "✅ Done! The connection string has been updated."
echo ""
echo "📋 Next steps:"
echo "1. Wait 1-2 minutes for the app to restart"
echo "2. Check the logs to verify the connection:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "3. Test the API endpoint:"
echo "   curl https://$APP_NAME.azurewebsites.net/health"
echo ""

# Optional: Show current app settings (without sensitive values)
echo "📄 Current app settings:"
az webapp config appsettings list \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "[?name=='LEAVE_DATABASE_URL'].{Name:name, Value:'***HIDDEN***'}" \
    --output table

echo ""
echo "🎉 Setup complete!"
