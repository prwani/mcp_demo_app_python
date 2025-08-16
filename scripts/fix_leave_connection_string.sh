#!/bin/bash

# Fix Leave App Connection String Issues

set -e

RESOURCE_GROUP="mcp-python-demo-rg-7859"
APP_NAME="mcp-leave-api-7859"
SQL_SERVER="leave-sql-server-7859"
DATABASE="leave_db"
SQL_ADMIN="sqladminuser"

echo "🔧 Fixing Leave App Connection String..."

# Option 1: Username/Password Authentication
echo "📋 Setting up Username/Password Authentication..."

# Prompt for SQL password
echo "Please enter the SQL admin password for user 'sqladminuser':"
read -s SQL_PASSWORD

# URL encode the password
ENCODED_PASSWORD=$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('$SQL_PASSWORD'))")

# Create proper SQLAlchemy connection string for username/password auth
CONNECTION_STRING="mssql+pyodbc://${SQL_ADMIN}:${ENCODED_PASSWORD}@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

echo "🔗 Setting connection string in Azure App Service..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings LEAVE_DATABASE_URL="$CONNECTION_STRING"

echo "✅ Connection string updated!"

# Option 2: Enable Managed Identity (commented out - uncomment if preferred)
# echo "🆔 Setting up Managed Identity Authentication..."
# 
# # Enable system-assigned managed identity
# az webapp identity assign \
#     --name $APP_NAME \
#     --resource-group $RESOURCE_GROUP
# 
# # Get the managed identity principal ID
# PRINCIPAL_ID=$(az webapp identity show --name $APP_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
# 
# # Add the managed identity as an Azure AD admin for the SQL server
# az sql server ad-admin create \
#     --resource-group $RESOURCE_GROUP \
#     --server-name $SQL_SERVER \
#     --display-name $APP_NAME \
#     --object-id $PRINCIPAL_ID
# 
# # Create connection string for managed identity
# MSI_CONNECTION_STRING="mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi"
# 
# # Set the managed identity connection string
# az webapp config appsettings set \
#     --name $APP_NAME \
#     --resource-group $RESOURCE_GROUP \
#     --settings LEAVE_DATABASE_URL="$MSI_CONNECTION_STRING" LEAVE_USE_MANAGED_IDENTITY="true"

echo "🚀 Restarting the web app..."
az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP

echo "✅ Done! Check the logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
