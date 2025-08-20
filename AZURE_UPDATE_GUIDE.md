# Azure Deployment Update Guide
## Fixing URL Encoding for Existing Deployment

Since you've already completed the Azure deployment, you only need to **update app settings** - no redeployment required!

## 🎯 **Quick Summary**
**Problem**: Connection strings with unencoded special characters (`@`, `!`) cause login timeouts  
**Solution**: Update app settings with URL-encoded connection strings  
**Impact**: Only API apps need config updates, no code changes or container rebuilds needed  

## 📋 **What Needs Updates**

### ✅ **Configuration Updates Only (No Redeployment)**
1. **Leave API app settings** - Update `LEAVE_DATABASE_URL`
2. **Timesheet API app settings** - Update `TIMESHEET_DATABASE_URL`

### ✅ **No Changes Needed**
- ❌ **Container images** - App code is correct, no rebuild needed
- ❌ **MCP servers** - They only call the APIs, not the database
- ❌ **Chat client** - Only connects to MCP servers
- ❌ **Database** - Schema and data are fine
- ❌ **Azure SQL firewall** - Already configured

## 🔧 **Step-by-Step Fix**

### **Option 1: Use the Automated Script (Recommended)**

1. **Update the script with your actual resource names:**
   ```bash
   cd /home/prwani_u/copilots_code/mcp_demo_app_python
   nano scripts/fix_azure_app_settings.sh
   ```

2. **Edit these variables in the script:**
   ```bash
   export RG="your-actual-resource-group"              # e.g., "mcp-python-demo-rg-1234"
   export LEAVE_API_APP="your-actual-leave-api-name"   # e.g., "mcp-leave-api-1234"
   export TIMESHEET_API_APP="your-actual-timesheet-api-name"  # e.g., "mcp-timesheet-api-1234"
   ```

3. **Run the script:**
   ```bash
   ./scripts/fix_azure_app_settings.sh
   ```

### **Option 2: Manual Azure CLI Commands**

If you prefer to run commands manually:

```bash
# Set your variables
export RG="your-resource-group"
export LEAVE_API_APP="your-leave-api-app"
export TIMESHEET_API_APP="your-timesheet-api-app"

# Option A: Use username/password (URL-encoded password)
# Generate URL-encoded connection strings
ENCODED_LEAVE_PASSWORD=$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('CHANGE_ME_str0ngP@ss!'))")
ENCODED_TIMESHEET_PASSWORD=$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('CHANGE_ME_str0ngP@ss!'))")

LEAVE_DATABASE_URL="mssql+pyodbc://sqladminuser:${ENCODED_LEAVE_PASSWORD}@leave-sql-server-1234.database.windows.net:1433/leave_db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"

TIMESHEET_DATABASE_URL="mssql+pyodbc://sqladminuser:${ENCODED_TIMESHEET_PASSWORD}@timesheet-sql-server-1234.database.windows.net:1433/timesheet_db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"

# Option B (recommended since you enabled Managed Identity): use App Service Managed Identity
# When using managed identity you should NOT include a username/password in the URL. Instead set
# the connection string to the same DSN but without credentials and add the Authentication parameter.
# Example:
LEAVE_DATABASE_URL_MI="mssql+pyodbc://@leave-sql-server-1234.database.windows.net:1433/leave_db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30&Authentication=ActiveDirectoryMsi"

# Note: To make the Python app use managed identity set the following app setting as well:
# LEAVE_USE_MANAGED_IDENTITY=1

# Update app settings
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
    LEAVE_DATABASE_URL="$LEAVE_DATABASE_URL"

az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
    TIMESHEET_DATABASE_URL="$TIMESHEET_DATABASE_URL"
```

## 🔍 **How to Find Your Resource Names**

If you don't remember your exact resource names:

```bash
# List your resource groups
az group list --query "[].name" -o table

# List web apps in your resource group
az webapp list -g "your-resource-group" --query "[].name" -o table

# Or find apps with specific patterns
az webapp list -g "your-resource-group" --query "[?contains(name, 'leave') || contains(name, 'timesheet')].{Name:name, ResourceGroup:resourceGroup}" -o table
```

## ⏱️ **Timeline**
- **Configuration update**: ~2 minutes
- **App restart**: ~1-2 minutes (automatic)
- **Total downtime**: ~3-4 minutes per API

## ✅ **Verification**

After updating the settings:

1. **Check if apps are running:**
   ```bash
   az webapp show -g "$RG" -n "$LEAVE_API_APP" --query "state" -o tsv
   az webapp show -g "$RG" -n "$TIMESHEET_API_APP" --query "state" -o tsv
   ```
   Should return: `Running`

2. **Test the APIs:**
   ```bash
   # Test Leave API (replace with your actual URL)
   curl https://your-leave-api-app.azurewebsites.net/health

   # Test Timesheet API (replace with your actual URL)  
   curl https://your-timesheet-api-app.azurewebsites.net/health
   ```

3. **Check app logs if needed:**
   ```bash
   az webapp log tail -g "$RG" -n "$LEAVE_API_APP"
   ```

## 🎯 **Expected Results**

After the fix:
- ✅ APIs can connect to Azure SQL without timeout errors
- ✅ MCP servers can successfully call the APIs
- ✅ Chat client can interact with both leave and timesheet data
- ✅ No more login timeout errors

## 🚨 **Troubleshooting**

If apps still have issues after the update:

1. **Check the updated connection string:**
   ```bash
   az webapp config appsettings list -g "$RG" -n "$LEAVE_API_APP" --query "[?name=='LEAVE_DATABASE_URL'].value" -o tsv
   ```

2. **Look for error logs:**
   ```bash
   az webapp log tail -g "$RG" -n "$LEAVE_API_APP"
   ```

3. **Restart the app manually if needed:**
   ```bash
   az webapp restart -g "$RG" -n "$LEAVE_API_APP"
   ```
