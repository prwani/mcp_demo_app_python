#!/bin/bash

# Deploy Leave App to Azure App Service (non-Docker)

set -e

# Configuration
SUFFIX="${SUFFIX:-1234}"
RESOURCE_GROUP="mcp-python-demo-rg-${SUFFIX}"
APP_NAME="mcp-leave-api-${SUFFIX}"
LOCATION="East US"
APP_SERVICE_PLAN="mcp-leave-plan-${SUFFIX}"

echo "🚀 Deploying Leave App to Azure App Service (non-Docker)..."

# Create App Service Plan if it doesn't exist
echo "📋 Creating/updating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location "$LOCATION" \
    --sku B1 \
    --is-linux

# Create/update the web app
echo "🌐 Creating/updating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "PYTHON|3.10"

# Configure startup command
echo "⚙️ Configuring startup command..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "python leave_app/startup.py"

# Set environment variables (you'll need to configure these)
echo "🔧 Setting environment variables..."
echo "⚠️  You need to set LEAVE_DATABASE_URL manually:"
echo "   az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings LEAVE_DATABASE_URL='your-connection-string'"

# Deploy the code
echo "📦 Deploying code..."
cd /home/prwani_u/copilots_code/mcp_demo_app_python
zip -r leave-app.zip . -x "*.git*" "*/__pycache__/*" "*.pyc"

az webapp deployment source config-zip \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --src leave-app.zip

echo "✅ Deployment complete!"
echo "🌐 App URL: https://$APP_NAME.azurewebsites.net"
echo ""
echo "📝 Next steps:"
echo "1. Set the LEAVE_DATABASE_URL environment variable"
echo "2. Check logs: az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo "3. Test the app: curl https://$APP_NAME.azurewebsites.net/health"
