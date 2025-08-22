# Azure Deployment Setup

This guide provides step-by-step instructions to deploy the MCP Demo App components to Azure using Azure CLI.

## Prerequisites
- Azure CLI installed ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- Azure subscription
- Python 3.8+
- Git

## 0. Configuration variables (recommended)
Define these once per shell session and use them throughout. Adjust the names as needed.
Tip: A 4-digit suffix is added to most resource names to avoid collisions when multiple users deploy in parallel.

```bash
# Unique suffix (4-digit, zero-padded) to avoid global name collisions
export SUFFIX=$(printf "%04d" $((RANDOM % 10000)))
echo "Using suffix: $SUFFIX"

# Core
export RG="mcp-python-demo-rg-$SUFFIX"
export REGION="eastus2"

# Azure Container Registry (ACR names must be lowercase alphanumeric; no hyphens)
export ACR_NAME="mcpdemoregistry$SUFFIX"

# App Service Plan and Web App names
export ASP_NAME="mcp-demo-asp-$SUFFIX"
export LEAVE_API_APP="mcp-leave-api-$SUFFIX"
export LEAVE_MCP_APP="mcp-leave-mcp-$SUFFIX"
export TIMESHEET_API_APP="mcp-timesheet-api-$SUFFIX"
export TIMESHEET_MCP_APP="mcp-timesheet-mcp-$SUFFIX"
export CHAT_CLIENT_APP="mcp-chat-client-$SUFFIX"

# Azure SQL (serverless) – Leave
export LEAVE_SQL_SERVER="leave-sql-server-$SUFFIX"
export LEAVE_SQL_DB="leave_db"
export LEAVE_SQL_ADMIN="sqladminuser"
export LEAVE_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"  # choose a strong password

# Azure SQL (serverless) – Timesheet
export TIMESHEET_SQL_SERVER="timesheet-sql-server-$SUFFIX"
export TIMESHEET_SQL_DB="timesheet_db"
export TIMESHEET_SQL_ADMIN="sqladminuser"
export TIMESHEET_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"  # choose a strong password

# Azure OpenAI (optional for chat intent)
export AOAI_ENDPOINT="https://pw-mcp-demo-foundry.cognitiveservices.azure.com/"
export AOAI_NAME="pw-mcp-demo-foundry"
export AOAI_API_VERSION="2025-04-01-preview"
export AOAI_DEPLOYMENT="gpt-5"

# Helpful derived values (set after resources exist)
# Azure Deployment Setup (Common)
```
This guide covers the common prerequisites and Azure resources used by all four deployment options. After completing these, follow one of:

- option_1_setup.md: SQLite + Zip Deploy (Web App runtime)
- option_2_setup.md: SQLite + Docker (Web App for Containers)
- option_3_setup.md: Azure SQL + Zip Deploy
- option_4_setup.md: Azure SQL + Docker

## Prerequisites
- Azure CLI installed
- Azure subscription
- Python 3.10+
- Docker (only for Docker options)

## 0. Configuration variables
Define once per session:

```bash
export SUFFIX=$(printf "%04d" $((RANDOM % 10000)))
export RG="mcp-python-demo-rg-$SUFFIX"
export REGION="eastus2"
export ASP_NAME="mcp-demo-asp-$SUFFIX"
export LEAVE_API_APP="mcp-leave-api-$SUFFIX"
export LEAVE_MCP_APP="mcp-leave-mcp-$SUFFIX"
export TIMESHEET_API_APP="mcp-timesheet-api-$SUFFIX"
export TIMESHEET_MCP_APP="mcp-timesheet-mcp-$SUFFIX"
export CHAT_CLIENT_APP="mcp-chat-client-$SUFFIX"
# ACR (docker options)
export ACR_NAME="mcpdemoregistry$SUFFIX"
```

## 1. Login and create Resource Group
```bash
az login
az group create --name "$RG" --location "$REGION"
```

## 2. Create App Service Plan (Linux)
```bash
az appservice plan create -g "$RG" -n "$ASP_NAME" --sku B1 --is-linux
```

## 3. (Optional) Azure SQL resources (only for options 3 and 4)
```bash
export LEAVE_SQL_SERVER="leave-sql-server-$SUFFIX"
export LEAVE_SQL_DB="leave_db"
export LEAVE_SQL_ADMIN="sqladminuser"
export LEAVE_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"

export TIMESHEET_SQL_SERVER="timesheet-sql-server-$SUFFIX"
export TIMESHEET_SQL_DB="timesheet_db"
export TIMESHEET_SQL_ADMIN="sqladminuser"
export TIMESHEET_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"

# Create servers and DBs
az sql server create --name "$LEAVE_SQL_SERVER" -g "$RG" -l "$REGION" -u "$LEAVE_SQL_ADMIN" -p "$LEAVE_SQL_PASSWORD"
az sql db create -g "$RG" -s "$LEAVE_SQL_SERVER" -n "$LEAVE_SQL_DB" --service-objective GP_S_Gen5_1

az sql server create --name "$TIMESHEET_SQL_SERVER" -g "$RG" -l "$REGION" -u "$TIMESHEET_SQL_ADMIN" -p "$TIMESHEET_SQL_PASSWORD"
az sql db create -g "$RG" -s "$TIMESHEET_SQL_SERVER" -n "$TIMESHEET_SQL_DB" --service-objective GP_S_Gen5_1
```
Note: Schema/seed steps are in the option-specific guides.

## 4. (Docker options only) ACR setup
```bash
az acr create -g "$RG" -n "$ACR_NAME" --sku Basic
az acr login -n "$ACR_NAME"
export ACR_LOGIN=$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)
```

## 5. Create Web Apps (names only; images or runtimes are set per option)
```bash
az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$CHAT_CLIENT_APP" --runtime "PYTHON|3.10"
```

## 6. Next steps
- Choose and follow one option guide from this repo root.
- Return here for shared troubleshooting and variables.
echo "Your public IP: $MY_IP"

# Allow your IP for Leave SQL Server
az sql server firewall-rule create \
	--resource-group "$RG" \
	--server "$LEAVE_SQL_SERVER" \
	--name "AllowMyIP" \
	--start-ip-address "$MY_IP" \
	--end-ip-address "$MY_IP"

# Allow your IP for Timesheet SQL Server
az sql server firewall-rule create \
	--resource-group "$RG" \
	--server "$TIMESHEET_SQL_SERVER" \
	--name "AllowMyIP" \
	--start-ip-address "$MY_IP" \
	--end-ip-address "$MY_IP"
```

> **Note:** Remove or restrict this rule after deployment for security.
### 3.1 Initialize schema and seed data
After the databases are created, run the schema and seed scripts.

Options:
- Use Azure Portal > your SQL database > Query editor (preview) to paste and run the contents of:
	- `leave_app/sql/schema.sql`, then `leave_app/sql/seed.sql` against the Leave DB
	- `timesheet_app/sql/schema.sql`, then `timesheet_app/sql/seed.sql` against the Timesheet DB
- Or use sqlcmd locally (requires ODBC driver and tools installed):

```bash
# Example for Leave DB (repeat similarly for Timesheet DB)
sqlcmd -S ${LEAVE_SQL_SERVER}.database.windows.net -d ${LEAVE_SQL_DB} -U ${LEAVE_SQL_ADMIN} -P ${LEAVE_SQL_PASSWORD} -i leave_app/sql/schema.sql
sqlcmd -S ${LEAVE_SQL_SERVER}.database.windows.net -d ${LEAVE_SQL_DB} -U ${LEAVE_SQL_ADMIN} -P ${LEAVE_SQL_PASSWORD} -i leave_app/sql/seed.sql
```

If sqlcmd isn't available, you can use the official tools container:
```bash
docker run --rm -it mcr.microsoft.com/mssql-tools \
	/opt/mssql-tools18/bin/sqlcmd -C -S ${LEAVE_SQL_SERVER}.database.windows.net -d ${LEAVE_SQL_DB} -U ${LEAVE_SQL_ADMIN} -P ${LEAVE_SQL_PASSWORD} -i /schema.sql
```
Mount the local file with -v and reference it at /schema.sql.

## 4. Deploy Web/API Apps to Azure Web Apps
Repeat for each app (leave, timesheet, chat):
```bash
az webapp up --name <app-name> --resource-group mcp-demo-rg --runtime "PYTHON|3.8"
```
Containerize and deploy via Azure Container Registry (ACR) and Web App for Containers.

Note: The following container-based steps are the recommended path. The "webapp up" command above is an alternative for non-container deployments.

Important when using Azure SQL from containers:
- Your API containers must include the Microsoft ODBC Driver 18 for SQL Server and unixODBC libraries, plus the pyodbc Python package.
- This repo’s default Dockerfiles are kept minimal. If you switch to Azure SQL, update the API Dockerfiles to install these system packages before pip installing requirements.

Example snippet to add near the top of API Dockerfiles (Debian 12/Bookworm):
```dockerfile
RUN apt-get update && apt-get install -y curl gnupg ca-certificates \
	&& mkdir -p /usr/share/keyrings \
	&& curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
	&& echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft-prod.list \
	&& apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
	&& rm -rf /var/lib/apt/lists/*

# Then ensure pyodbc is installed (either add to requirements.txt or pip install pyodbc)
```

### 4.1 Create Azure Container Registry
```bash
az acr create -g mcp-demo-rg -n <acrName> --sku Basic
az acr login -n <acrName>
ACR_LOGIN=$(az acr show -n <acrName> --query loginServer -o tsv)
```

Using variables:
```bash
az acr create -g "$RG" -n "$ACR_NAME" --sku Basic
az acr login -n "$ACR_NAME"
export ACR_LOGIN=$(az acr show -n "$ACR_NAME" --query loginServer -o tsv)
echo "ACR login server: $ACR_LOGIN"
```

### 4.2 Build and Push Images (ACR)
```bash
# Leave API
az acr build -r <acrName> -t $ACR_LOGIN/leave-api:latest -f leave_app/Dockerfile.api .
# Leave MCP
az acr build -r <acrName> -t $ACR_LOGIN/leave-mcp:latest -f leave_app/Dockerfile.mcp .
# Timesheet API
az acr build -r <acrName> -t $ACR_LOGIN/timesheet-api:latest -f timesheet_app/Dockerfile.api .
# Timesheet MCP
az acr build -r <acrName> -t $ACR_LOGIN/timesheet-mcp:latest -f timesheet_app/Dockerfile.mcp .
# Chat Client
az acr build -r <acrName> -t $ACR_LOGIN/chat-client:latest -f chat_client/Dockerfile .
```

Using variables:
```bash
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/leave-api:latest" -f leave_app/Dockerfile.api .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/leave-mcp:latest" -f leave_app/Dockerfile.mcp .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/timesheet-api:latest" -f timesheet_app/Dockerfile.api .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/timesheet-mcp:latest" -f timesheet_app/Dockerfile.mcp .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/chat-client:latest" -f chat_client/Dockerfile .
```
Note:
- The --deployment-container-image-name flag is deprecated. Create the app first, assign identity and AcrPull, then set the image using az webapp config container set as shown above. This avoids ACR credential errors.

### 4.3 Create App Services for Containers
```bash
# App Service Plan (Linux)
az appservice plan create -g mcp-demo-rg -n mcp-demo-asp --sku B1 --is-linux

# Web apps (create first; set image in a later step)
az webapp create -g mcp-demo-rg -p mcp-demo-asp -n <leaveApiApp> --runtime "PYTHON|3.10"
az webapp create -g mcp-demo-rg -p mcp-demo-asp -n <leaveMcpApp> --runtime "PYTHON|3.10"
az webapp create -g mcp-demo-rg -p mcp-demo-asp -n <timesheetApiApp> --runtime "PYTHON|3.10"
az webapp create -g mcp-demo-rg -p mcp-demo-asp -n <timesheetMcpApp> --runtime "PYTHON|3.10"
az webapp create -g mcp-demo-rg -p mcp-demo-asp -n <chatClientApp> --runtime "PYTHON|3.10"
```

Using variables:
```bash
az appservice plan create -g "$RG" -n "$ASP_NAME" --sku B1 --is-linux

az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$LEAVE_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_API_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$TIMESHEET_MCP_APP" --runtime "PYTHON|3.10"
az webapp create -g "$RG" -p "$ASP_NAME" -n "$CHAT_CLIENT_APP" --runtime "PYTHON|3.10"
```

Note:
- Recent Azure CLI versions require specifying an initial runtime or container at creation time. We set a temporary runtime (PYTHON|3.10) to create the apps, then in step 4.6 we switch each app to its container image. If you encounter a runtime/container conflict later, use the provided "Clear conflicting runtime settings" commands before setting the container image.

### 4.4 Grant Web Apps access to ACR (Managed Identity recommended)
```bash
# Enable system-managed identity
for app in <leaveApiApp> <leaveMcpApp> <timesheetApiApp> <timesheetMcpApp> <chatClientApp>; do
	az webapp identity assign -g mcp-demo-rg -n $app
done

# Grant AcrPull to each web app identity
ACR_ID=$(az acr show -n <acrName> --query id -o tsv)
for app in <leaveApiApp> <leaveMcpApp> <timesheetApiApp> <timesheetMcpApp> <chatClientApp>; do
	PRIN_ID=$(az webapp identity show -g mcp-demo-rg -n $app --query principalId -o tsv)
	az role assignment create --assignee $PRIN_ID --role AcrPull --scope $ACR_ID
done
```

Using variables:
```bash
for app in "$LEAVE_API_APP" "$LEAVE_MCP_APP" "$TIMESHEET_API_APP" "$TIMESHEET_MCP_APP" "$CHAT_CLIENT_APP"; do
	az webapp identity assign -g "$RG" -n "$app"
done

export ACR_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv)
for app in "$LEAVE_API_APP" "$LEAVE_MCP_APP" "$TIMESHEET_API_APP" "$TIMESHEET_MCP_APP" "$CHAT_CLIENT_APP"; do
	PRIN_ID=$(az webapp identity show -g "$RG" -n "$app" --query principalId -o tsv)
	az role assignment create --assignee "$PRIN_ID" --role AcrPull --scope "$ACR_ID"
done
```

### 4.5 Configure App Settings
```bash
# Leave API env (Azure SQL connection & container port)
az webapp config appsettings set -g mcp-demo-rg -n <leaveApiApp> --settings \
	LEAVE_DATABASE_URL="<leave-conn-string>" \
	WEBSITES_PORT="8001"

# Timesheet API env
az webapp config appsettings set -g mcp-demo-rg -n <timesheetApiApp> --settings \
	TIMESHEET_DATABASE_URL="<timesheet-conn-string>" \
	WEBSITES_PORT="8002"

# Leave MCP points to Leave API
az webapp config appsettings set -g mcp-demo-rg -n <leaveMcpApp> --settings \
	LEAVE_API_URL="https://<leaveApiApp>.azurewebsites.net" \
	WEBSITES_PORT="8011"

# Timesheet MCP points to Timesheet API
az webapp config appsettings set -g mcp-demo-rg -n <timesheetMcpApp> --settings \
	TIMESHEET_API_URL="https://<timesheetApiApp>.azurewebsites.net" \
	WEBSITES_PORT="8012"

# Chat Client points to MCPs and OpenAI
az webapp config appsettings set -g mcp-demo-rg -n <chatClientApp> --settings \
	LEAVE_MCP_URL="https://<leaveMcpApp>.azurewebsites.net" \
	TIMESHEET_MCP_URL="https://<timesheetMcpApp>.azurewebsites.net" \
	AZURE_OPENAI_ENDPOINT="<aoai-endpoint>" \
	AZURE_OPENAI_KEY="<aoai-key>" \
	AZURE_OPENAI_API_VERSION="2024-05-01-preview" \
	AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
	WEBSITES_PORT="8000"

```

Using variables:
```bash
# Leave API
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
	LEAVE_DATABASE_URL="$LEAVE_DATABASE_URL" \
	WEBSITES_PORT="8001"

# Timesheet API
az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
	TIMESHEET_DATABASE_URL="$TIMESHEET_DATABASE_URL" \
	WEBSITES_PORT="8002"

# Leave MCP points to Leave API
az webapp config appsettings set -g "$RG" -n "$LEAVE_MCP_APP" --settings \
	LEAVE_API_URL="https://${LEAVE_API_APP}.azurewebsites.net" \
	WEBSITES_PORT="8011"

# Timesheet MCP points to Timesheet API
az webapp config appsettings set -g "$RG" -n "$TIMESHEET_MCP_APP" --settings \
	TIMESHEET_API_URL="https://${TIMESHEET_API_APP}.azurewebsites.net" \
	WEBSITES_PORT="8012"

# Chat Client points to MCPs and OpenAI
az webapp config appsettings set -g "$RG" -n "$CHAT_CLIENT_APP" --settings \
	LEAVE_MCP_URL="https://${LEAVE_MCP_APP}.azurewebsites.net" \
	TIMESHEET_MCP_URL="https://${TIMESHEET_MCP_APP}.azurewebsites.net" \
	AZURE_OPENAI_ENDPOINT="$AOAI_ENDPOINT" \
	AZURE_OPENAI_KEY="$AOAI_KEY" \
	AZURE_OPENAI_API_VERSION="$AOAI_API_VERSION" \
	AZURE_OPENAI_DEPLOYMENT="$AOAI_DEPLOYMENT" \
	WEBSITES_PORT="8000"
```

### 4.6 Configure container images (single container, with Managed Identity)

Recommended (single-container image via linux-fx-version):
```bash
az webapp config set -g mcp-demo-rg -n <leaveApiApp> --linux-fx-version "DOCKER|$ACR_LOGIN/leave-api:latest"
az webapp config set -g mcp-demo-rg -n <leaveMcpApp> --linux-fx-version "DOCKER|$ACR_LOGIN/leave-mcp:latest"
az webapp config set -g mcp-demo-rg -n <timesheetApiApp> --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-api:latest"
az webapp config set -g mcp-demo-rg -n <timesheetMcpApp> --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-mcp:latest"
az webapp config set -g mcp-demo-rg -n <chatClientApp> --linux-fx-version "DOCKER|$ACR_LOGIN/chat-client:latest"
```

Using variables:
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/leave-api:latest"
az webapp config set -g "$RG" -n "$LEAVE_MCP_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/leave-mcp:latest"
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-api:latest"
az webapp config set -g "$RG" -n "$TIMESHEET_MCP_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-mcp:latest"
az webapp config set -g "$RG" -n "$CHAT_CLIENT_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/chat-client:latest"
```

Alternate (legacy) method using container set:
```bash
az webapp config container set -g mcp-demo-rg -n <leaveApiApp> --docker-custom-image-name $ACR_LOGIN/leave-api:latest --docker-registry-server-url https://$ACR_LOGIN
az webapp config container set -g mcp-demo-rg -n <leaveMcpApp> --docker-custom-image-name $ACR_LOGIN/leave-mcp:latest --docker-registry-server-url https://$ACR_LOGIN
az webapp config container set -g mcp-demo-rg -n <timesheetApiApp> --docker-custom-image-name $ACR_LOGIN/timesheet-api:latest --docker-registry-server-url https://$ACR_LOGIN
az webapp config container set -g mcp-demo-rg -n <timesheetMcpApp> --docker-custom-image-name $ACR_LOGIN/timesheet-mcp:latest --docker-registry-server-url https://$ACR_LOGIN
az webapp config container set -g mcp-demo-rg -n <chatClientApp> --docker-custom-image-name $ACR_LOGIN/chat-client:latest --docker-registry-server-url https://$ACR_LOGIN
```

Using variables:
```bash
az webapp config container set -g "$RG" -n "$LEAVE_API_APP" --docker-custom-image-name "$ACR_LOGIN/leave-api:latest" --docker-registry-server-url "https://$ACR_LOGIN"
az webapp config container set -g "$RG" -n "$LEAVE_MCP_APP" --docker-custom-image-name "$ACR_LOGIN/leave-mcp:latest" --docker-registry-server-url "https://$ACR_LOGIN"
az webapp config container set -g "$RG" -n "$TIMESHEET_API_APP" --docker-custom-image-name "$ACR_LOGIN/timesheet-api:latest" --docker-registry-server-url "https://$ACR_LOGIN"
az webapp config container set -g "$RG" -n "$TIMESHEET_MCP_APP" --docker-custom-image-name "$ACR_LOGIN/timesheet-mcp:latest" --docker-registry-server-url "https://$ACR_LOGIN"
az webapp config container set -g "$RG" -n "$CHAT_CLIENT_APP" --docker-custom-image-name "$ACR_LOGIN/chat-client:latest" --docker-registry-server-url "https://$ACR_LOGIN"
```

Optional: enable Managed Identity for ACR pulls explicitly (safe to re-run):
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --generic-configurations '{"acrUseManagedIdentityCreds": true}'
az webapp config set -g "$RG" -n "$LEAVE_MCP_APP" --generic-configurations '{"acrUseManagedIdentityCreds": true}'
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --generic-configurations '{"acrUseManagedIdentityCreds": true}'
az webapp config set -g "$RG" -n "$TIMESHEET_MCP_APP" --generic-configurations '{"acrUseManagedIdentityCreds": true}'
az webapp config set -g "$RG" -n "$CHAT_CLIENT_APP" --generic-configurations '{"acrUseManagedIdentityCreds": true}'
```

Troubleshooting (if you see multicontainer/runtime conflicts):
```bash
# Verify Linux plan and Linux app
az appservice plan show -g "$RG" -n "$ASP_NAME" --query reserved -o tsv    # should be true
az webapp show -g "$RG" -n "$LEAVE_API_APP" --query kind -o tsv            # should contain "linux"

# Clear conflicting runtime settings, then set image again
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --generic-configurations '{"linuxFxVersion": null, "windowsFxVersion": null, "appCommandLine": null}'
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/leave-api:latest"
```

### 4.7 Update to latest container image (CI/CD or manual)
```bash
az webapp config container set -g mcp-demo-rg -n <leaveApiApp> --docker-custom-image-name $ACR_LOGIN/leave-api:latest
az webapp config container set -g mcp-demo-rg -n <leaveMcpApp> --docker-custom-image-name $ACR_LOGIN/leave-mcp:latest
az webapp config container set -g mcp-demo-rg -n <timesheetApiApp> --docker-custom-image-name $ACR_LOGIN/timesheet-api:latest
az webapp config container set -g mcp-demo-rg -n <timesheetMcpApp> --docker-custom-image-name $ACR_LOGIN/timesheet-mcp:latest
az webapp config container set -g mcp-demo-rg -n <chatClientApp> --docker-custom-image-name $ACR_LOGIN/chat-client:latest
```

Using variables:
```bash
az webapp config container set -g "$RG" -n "$LEAVE_API_APP" --docker-custom-image-name "$ACR_LOGIN/leave-api:latest"
az webapp config container set -g "$RG" -n "$LEAVE_MCP_APP" --docker-custom-image-name "$ACR_LOGIN/leave-mcp:latest"
az webapp config container set -g "$RG" -n "$TIMESHEET_API_APP" --docker-custom-image-name "$ACR_LOGIN/timesheet-api:latest"
az webapp config container set -g "$RG" -n "$TIMESHEET_MCP_APP" --docker-custom-image-name "$ACR_LOGIN/timesheet-mcp:latest"
az webapp config container set -g "$RG" -n "$CHAT_CLIENT_APP" --docker-custom-image-name "$ACR_LOGIN/chat-client:latest"
```

### (Optional) Local Docker build and run
```bash
# Build
docker build -t leave-api -f leave_app/Dockerfile.api .
docker build -t leave-mcp -f leave_app/Dockerfile.mcp .
docker build -t timesheet-api -f timesheet_app/Dockerfile.api .
docker build -t timesheet-mcp -f timesheet_app/Dockerfile.mcp .
docker build -t chat-client -f chat_client/Dockerfile .

# Run
docker run -p 8001:8001 -e LEAVE_DATABASE_URL="sqlite:////data/leave.db" -v $(pwd)/data:/data leave-api
docker run -p 8011:8011 -e LEAVE_API_URL="http://host.docker.internal:8001" leave-mcp
docker run -p 8002:8002 -e TIMESHEET_DATABASE_URL="sqlite:////data/timesheet.db" -v $(pwd)/data:/data timesheet-api
docker run -p 8012:8012 -e TIMESHEET_API_URL="http://host.docker.internal:8002" timesheet-mcp
docker run -p 8000:8000 -e LEAVE_MCP_URL="http://host.docker.internal:8011" -e TIMESHEET_MCP_URL="http://host.docker.internal:8012" chat-client
```

## 5. Set Up Azure OpenAI
- Request access to Azure OpenAI ([Azure OpenAI Service](https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/))
- Create resource:
```bash
az cognitiveservices account create --name <openai-name> --resource-group mcp-demo-rg --kind OpenAI --sku S0 --location eastus
```

Using variables:
```bash
az cognitiveservices account create \
	--name "$AOAI_NAME" \
	--resource-group "$RG" \
	--kind OpenAI \
	--sku S0 \
	--location "$REGION"

# After creation, set these for app settings (retrieve actual values from the resource):
# export AOAI_ENDPOINT="https://$AOAI_NAME.openai.azure.com/"
# export AOAI_KEY=$(az cognitiveservices account keys list -n "$AOAI_NAME" -g "$RG" --query key1 -o tsv)
```

## 6. Configure Environment Variables
Set connection strings and keys for each app:
- Azure SQL DB connection string
- Azure OpenAI endpoint and key

## 7. Update App Service Settings
```bash
az webapp config appsettings set --name <app-name> --resource-group mcp-demo-rg --settings KEY=VALUE
```

## 8. Verify Deployment
- Access web apps via Azure Portal or public URLs
- Test API endpoints and chat client

## References
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)
- [Azure SQL Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Azure Web Apps Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/overview)
