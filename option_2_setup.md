# Option 2: SQLite + Docker (Web App for Containers)

Use SQLite for both APIs; deploy container images from ACR.

## Prereqs
- Complete Azure_setup.md (0-5) including ACR (section 4).

## 1. Build and push images
```bash
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/leave-api:sqlite" -f leave_app/Dockerfile.api .
az acr build -r "$ACR_NAME" -t "$ACR_LOGIN/timesheet-api:sqlite" -f timesheet_app/Dockerfile.api .
```

## 2. App settings and identity
```bash
# Assign identity and ACR pull
for app in "$LEAVE_API_APP" "$TIMESHEET_API_APP"; do
  az webapp identity assign -g "$RG" -n "$app"
  PRIN_ID=$(az webapp identity show -g "$RG" -n "$app" --query principalId -o tsv)
  ACR_ID=$(az acr show -n "$ACR_NAME" --query id -o tsv)
  az role assignment create --assignee "$PRIN_ID" --role AcrPull --scope "$ACR_ID"
  az webapp config appsettings set -g "$RG" -n "$app" --settings WEBSITES_PORT="8001"
done
# Specific ports
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings LEAVE_DB_PROVIDER="sqlite" WEBSITES_PORT="8001"
az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings TIMESHEET_DB_PROVIDER="sqlite" WEBSITES_PORT="8002"
```

## 3. Configure container images
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/leave-api:sqlite"
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --linux-fx-version "DOCKER|$ACR_LOGIN/timesheet-api:sqlite"
```

## 4. Verify
- https://$LEAVE_API_APP.azurewebsites.net/health
- https://$TIMESHEET_API_APP.azurewebsites.net/health
