#!/bin/bash

# Quick fix for Leave App Connection String
# This addresses the Authentication conflict issue

set -e

RESOURCE_GROUP="mcp-python-demo-rg-7859"
APP_NAME="mcp-leave-api-7859"
SQL_SERVER="leave-sql-server-7859"
DATABASE="leave_db"
SQL_ADMIN="sqladminuser"

echo "🔧 Quick fix for Leave App Connection String..."

# Get the current connection string to see what we're working with
echo "📋 Current connection string:"
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[?name=='LEAVE_DATABASE_URL'].value" -o tsv

echo ""
echo "🔄 Choose authentication method:"
echo "1) Username/Password (requires SQL password)"
echo "2) Managed Identity (more secure, requires setup)"
read -p "Enter choice (1 or 2): " AUTH_CHOICE

if [ "$AUTH_CHOICE" = "1" ]; then
    echo "📝 Username/Password Authentication"
    echo "Enter SQL admin password for user '$SQL_ADMIN':"
    read -s SQL_PASSWORD
    
    # URL encode the password
    ENCODED_PASSWORD=$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('$SQL_PASSWORD'))")
    
    # Create proper connection string WITHOUT Authentication parameter
    CONNECTION_STRING="mssql+pyodbc://${SQL_ADMIN}:${ENCODED_PASSWORD}@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"
    
    echo "🔗 Setting username/password connection string..."
    az webapp config appsettings set \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --settings LEAVE_DATABASE_URL="$CONNECTION_STRING" LEAVE_USE_MANAGED_IDENTITY="false"

elif [ "$AUTH_CHOICE" = "2" ]; then
    echo "🆔 Managed Identity Authentication"
    
    # Enable system-assigned managed identity
    echo "Enabling managed identity..."
    az webapp identity assign \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP
    
    # Create connection string for managed identity (no username/password)
    MSI_CONNECTION_STRING="mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi"
    
    echo "🔗 Setting managed identity connection string..."
    az webapp config appsettings set \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --settings LEAVE_DATABASE_URL="$MSI_CONNECTION_STRING" LEAVE_USE_MANAGED_IDENTITY="true"
        
    echo "⚠️  You'll need to add the managed identity as Azure AD admin for SQL Server manually:"
    echo "   1. Go to Azure Portal > SQL Server > Active Directory admin"
    echo "   2. Add the app '$APP_NAME' as admin"
else
    echo "❌ Invalid choice"
    exit 1
fi

echo "🚀 Restarting the web app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

echo "✅ Done! Check the logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
