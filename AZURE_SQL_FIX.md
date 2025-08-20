# Azure SQL Entra Authentication Setup

## Problem
The Leave API web app (`mcp-leave-api-1234`) is failing to connect to Azure SQL because the database only allows Entra (Azure AD) based authentication, but the app is configured for username/password authentication.

## Root Cause
The Azure SQL database has been configured to only allow Entra (Azure AD) authentication. This means:
- Username/password authentication is disabled
- Only managed identity or Azure AD user authentication is allowed
- Connection strings must use `Authentication=ActiveDirectoryMsi`

## Solution

### Option 1: Automated Entra Setup Script (Recommended)
Run the automated Entra authentication setup script:
```bash
./setup_entra_auth.sh
```

This script will:
1. Enable system-assigned managed identity for the web app
2. Add the managed identity as Azure AD admin for the SQL server
3. Create a proper connection string with `Authentication=ActiveDirectoryMsi`
4. Update the Azure App Service settings
5. Restart the web app

### Option 2: Manual Entra Setup via Azure CLI
```bash
# Set your resource group and app name
RESOURCE_GROUP="mcp-python-demo-rg-1234"
APP_NAME="mcp-leave-api-1234"
SQL_SERVER="leave-sql-server-1234"
DATABASE="leave_db"

# Enable managed identity
PRINCIPAL_ID=$(az webapp identity assign \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId --output tsv)

# Add managed identity as Azure AD admin
az sql server ad-admin create \
    --resource-group "$RESOURCE_GROUP" \
    --server-name "$SQL_SERVER" \
    --display-name "$APP_NAME" \
    --object-id "$PRINCIPAL_ID"

# Create managed identity connection string
MSI_CONNECTION_STRING="mssql+pyodbc://@${SQL_SERVER}.database.windows.net:1433/${DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi"

# Update app settings
az webapp config appsettings set \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        LEAVE_DATABASE_URL="$MSI_CONNECTION_STRING" \
        LEAVE_USE_MANAGED_IDENTITY="true"

# Restart the app
az webapp restart --name "$APP_NAME" --resource-group "$RESOURCE_GROUP"
```

### Option 3: Azure Portal Setup
1. **Enable Managed Identity:**
    - Go to Azure Portal → App Services → `mcp-leave-api-1234`
   - Navigate to Identity → System assigned → Set Status to "On"
   - Note the Object (principal) ID

2. **Configure SQL Server Azure AD Admin:**
    - Go to Azure Portal → SQL servers → `leave-sql-server-1234`
   - Navigate to Azure Active Directory → Set admin
   - Add the web app's managed identity as admin

3. **Update Connection String:**
    - Go to App Services → `mcp-leave-api-1234` → Configuration
   - Update `LEAVE_DATABASE_URL` to:
     ```
    mssql+pyodbc://@leave-sql-server-1234.database.windows.net:1433/leave_db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30&Authentication=ActiveDirectoryMsi
     ```
   - Add `LEAVE_USE_MANAGED_IDENTITY=true`
   - Save and restart the app

## Key Points for Entra Authentication
- **No username/password**: The connection string should not contain credentials
- **Managed Identity required**: The web app must have system-assigned managed identity enabled
- **Azure AD admin**: The managed identity must be configured as Azure AD admin on the SQL server
- **Authentication parameter**: Must use `Authentication=ActiveDirectoryMsi`
- **No conflicting parameters**: Remove any `Integrated Security` or `Trusted_Connection` parameters

## Verification
After applying the Entra authentication setup:
1. Check the logs: `az webapp log tail --name mcp-leave-api-1234 --resource-group mcp-python-demo-rg-1234`
2. Test the API: `curl https://mcp-leave-api-1234.azurewebsites.net/health`
3. Look for "Database connection successful!" and "Using managed identity authentication" in the logs

## Prevention
To avoid authentication issues in Entra-only databases:
- Always use managed identity for App Service to Azure SQL connections
- Never include username/password in connection strings for Entra-only databases
- Ensure `Authentication=ActiveDirectoryMsi` is specified
- Remove any `Integrated Security` or `Trusted_Connection` parameters

## Files Modified
- `leave_app/api/db.py` - Enhanced for Entra authentication and better error diagnostics
- `setup_entra_auth.sh` - Automated Entra authentication setup script
- `AZURE_SQL_FIX.md` - Updated documentation for Entra authentication

## Troubleshooting
If you still see authentication errors:
1. Verify the managed identity is enabled: `az webapp identity show --name mcp-leave-api-1234 --resource-group mcp-python-demo-rg-1234`
2. Check if the identity is added as Azure AD admin: `az sql server ad-admin list --server leave-sql-server-1234 --resource-group mcp-python-demo-rg-1234`
3. Ensure the connection string doesn't contain username/password
4. Verify `Authentication=ActiveDirectoryMsi` is in the connection string
