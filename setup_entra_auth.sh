#!/bin/bash

# Setup Entra (Azure AD) Authentication for Leave API
# This script configures managed identity authentication for an Entra-only Azure SQL database

set -e

# Configuration - Update these values to match your deployment
RESOURCE_GROUP="mcp-python-demo-rg-7859"
APP_NAME="mcp-leave-api-7859"
SQL_SERVER="leave-sql-server-7859"
DATABASE="leave_db"

echo "🔧 Setting up Entra (Azure AD) Authentication for Leave API..."
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
echo "🆔 Step 1: Enable system-assigned managed identity for the web app..."

# Enable system-assigned managed identity
PRINCIPAL_ID=$(az webapp identity assign \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId \
    --output tsv)

if [ -z "$PRINCIPAL_ID" ]; then
    echo "❌ Failed to enable managed identity"
    exit 1
fi

echo "✅ Managed identity enabled. Principal ID: $PRINCIPAL_ID"

echo ""
echo "🔑 Step 2: Add managed identity as Azure AD admin for SQL Server..."

# Get the app's display name for the AD admin
APP_DISPLAY_NAME="$APP_NAME"

# Set the managed identity as Azure AD admin for the SQL server
az sql server ad-admin create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$SQL_SERVER" \
    --display-name "$APP_DISPLAY_NAME" \
    --object-id "$PRINCIPAL_ID"

echo "✅ Managed identity added as Azure AD admin for SQL Server"

echo ""
echo "🔗 Step 3: Creating managed identity connection string..."

# Create connection string for managed identity (no username/password)
MSI_CONNECTION_STRING="mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi"

echo "✅ Managed identity connection string created"

echo ""
echo "🚀 Step 4: Updating Azure App Service settings..."

# Update the app settings
az webapp config appsettings set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        LEAVE_DATABASE_URL="$MSI_CONNECTION_STRING" \
        LEAVE_USE_MANAGED_IDENTITY="true" \
    --output table

echo ""
echo "🔄 Step 5: Restarting the web app to apply changes..."
az webapp restart \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP"

echo ""
echo "✅ Done! Entra authentication has been configured."
echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for the app to restart and authenticate"
echo "2. Check the logs to verify the connection:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "3. Test the API endpoint:"
echo "   curl https://$APP_NAME.azurewebsites.net/health"
echo ""

echo "📄 Current authentication settings:"
az webapp config appsettings list \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "[?contains(name, 'LEAVE_')].{Name:name, Value:value}" \
    --output table

echo ""
echo "🔐 Security Notes:"
echo "- The app now uses its managed identity to authenticate to Azure SQL"
echo "- No passwords are stored in the connection string"
echo "- Authentication is handled automatically by Azure"
echo ""
echo "🎉 Entra authentication setup complete!"
