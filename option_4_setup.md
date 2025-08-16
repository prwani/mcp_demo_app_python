# Option 4: Azure SQL + Docker

Use Azure SQL for both APIs with container deployments.

## Prereqs
- Complete Azure_setup.md (0-5) including ACR.
- ODBC driver is already installed in provided Dockerfiles.

## 1. Build and push images
```bash
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/leave-api:mssql" -f leave_app/Dockerfile.api .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/timesheet-api:mssql" -f timesheet_app/Dockerfile.api .
```

## 2. App settings and identity
```bash
for app in "$LEAVE_API_APP" "$TIMESHEET_API_APP"; do
  az webapp identity assign -g "$RG" -n "$app"
  PRIN_ID=$(az webapp identity show -g "$RG" -n "$app" --query principalId -o tsv)
  ACR_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv)
  az role assignment create --assignee "$PRIN_ID" --role AcrPull --scope "$ACR_ID"
  az webapp config appsettings set -g "$RG" -n "$app" --settings WEBSITES_PORT="8001"
done

az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
  LEAVE_DB_PROVIDER="mssql" \
  LEAVE_DATABASE_URL="$LEAVE_DATABASE_URL" \
  WEBSITES_PORT="8001"

az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
  TIMESHEET_DB_PROVIDER="mssql" \
  TIMESHEET_DATABASE_URL="$TIMESHEET_DATABASE_URL" \
  WEBSITES_PORT="8002"
```

## 3. Configure images
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/leave-api:mssql"
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-api:mssql"
```

## 4. Schema/Seed
Run the SQL scripts as in option 3.

## 5. Verify /health endpoints
