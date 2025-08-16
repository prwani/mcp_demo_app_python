# Option 1: SQLite + Zip Deploy (Web App runtime)

This path uses SQLite for both APIs and deploys code as Zip packages to Azure Web Apps running Python.

## Prereqs
- Complete Azure_setup.md (common steps 0-2 and 5). SQL steps are NOT needed.

## 1. App settings
Set provider to SQLite (auto also works by default) and ports.
```bash
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
  LEAVE_DB_PROVIDER="sqlite" \
  WEBSITES_PORT="8001"

az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
  TIMESHEET_DB_PROVIDER="sqlite" \
  WEBSITES_PORT="8002"
```

## 2. Package and deploy (Zip)
Use built-in Oryx build from Zip.
```bash
# Leave API
zip -r leave_api.zip leave_app requirements.txt oryx.ini
az webapp deploy --resource-group "$RG" --name "$LEAVE_API_APP" --src-path leave_api.zip --type zip

# Timesheet API
zip -r timesheet_api.zip timesheet_app requirements.txt oryx.ini
az webapp deploy --resource-group "$RG" --name "$TIMESHEET_API_APP" --src-path timesheet_api.zip --type zip
```

## 3. Configure startup command (non-Docker)
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --startup-file "python -m leave_app.startup"
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --startup-file "python -m timesheet_app.startup"
```

## 4. Verify
- Hit https://$LEAVE_API_APP.azurewebsites.net/health
- Hit https://$TIMESHEET_API_APP.azurewebsites.net/health

SQLite database files persist under /home/site/data.
