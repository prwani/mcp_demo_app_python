#!/bin/bash

# Test Entra Authentication Setup for Leave API

set -e

RESOURCE_GROUP="mcp-python-demo-rg-7859"
APP_NAME="mcp-leave-api-7859"
SQL_SERVER="leave-sql-server-7859"

echo "🧪 Testing Entra Authentication Setup..."
echo ""

echo "1️⃣ Checking managed identity status..."
IDENTITY_STATUS=$(az webapp identity show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query principalId -o tsv 2>/dev/null || echo "not-enabled")

if [ "$IDENTITY_STATUS" = "not-enabled" ] || [ -z "$IDENTITY_STATUS" ]; then
    echo "❌ Managed identity is not enabled"
    exit 1
else
    echo "✅ Managed identity is enabled: $IDENTITY_STATUS"
fi

echo ""
echo "2️⃣ Checking Azure AD admin configuration..."
AD_ADMIN=$(az sql server ad-admin list --server "$SQL_SERVER" --resource-group "$RESOURCE_GROUP" --query "[0].login" -o tsv 2>/dev/null || echo "not-configured")

if [ "$AD_ADMIN" = "not-configured" ] || [ -z "$AD_ADMIN" ]; then
    echo "❌ Azure AD admin is not configured"
    exit 1
else
    echo "✅ Azure AD admin is configured: $AD_ADMIN"
fi

echo ""
echo "3️⃣ Checking app settings..."
DATABASE_URL=$(az webapp config appsettings list --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "[?name=='LEAVE_DATABASE_URL'].value" -o tsv 2>/dev/null || echo "not-set")
MSI_SETTING=$(az webapp config appsettings list --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query "[?name=='LEAVE_USE_MANAGED_IDENTITY'].value" -o tsv 2>/dev/null || echo "not-set")

if [[ "$DATABASE_URL" == *"Authentication=ActiveDirectoryMsi"* ]]; then
    echo "✅ Database URL contains correct authentication method"
else
    echo "❌ Database URL does not contain ActiveDirectoryMsi authentication"
    echo "Current URL pattern: ${DATABASE_URL:0:50}..."
fi

if [ "$MSI_SETTING" = "true" ]; then
    echo "✅ Managed identity setting is enabled"
else
    echo "⚠️  Managed identity setting is: $MSI_SETTING"
fi

echo ""
echo "4️⃣ Testing app availability..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_NAME.azurewebsites.net/" --connect-timeout 10 || echo "timeout")

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
    echo "✅ App is responding (HTTP $HTTP_STATUS)"
elif [ "$HTTP_STATUS" = "timeout" ]; then
    echo "⏱️  App connection timeout (may still be starting up)"
else
    echo "⚠️  App returned HTTP $HTTP_STATUS"
fi

echo ""
echo "📊 Summary:"
echo "- Managed Identity: $([ "$IDENTITY_STATUS" != "not-enabled" ] && echo "✅ Enabled" || echo "❌ Disabled")"
echo "- Azure AD Admin: $([ "$AD_ADMIN" != "not-configured" ] && echo "✅ Configured" || echo "❌ Not configured")"
echo "- Connection String: $([ "$DATABASE_URL" == *"ActiveDirectoryMsi"* ] && echo "✅ Correct" || echo "❌ Incorrect")"
echo "- App Status: $([ "$HTTP_STATUS" = "200" ] && echo "✅ Running" || echo "⚠️  Check logs")"

echo ""
if [ "$IDENTITY_STATUS" != "not-enabled" ] && [ "$AD_ADMIN" != "not-configured" ] && [[ "$DATABASE_URL" == *"ActiveDirectoryMsi"* ]]; then
    echo "🎉 Entra authentication is properly configured!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Wait a few minutes for the app to fully restart"
    echo "2. Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
    echo "3. Test API: curl https://$APP_NAME.azurewebsites.net/health"
else
    echo "⚠️  Configuration issues detected. Please review the setup."
fi
