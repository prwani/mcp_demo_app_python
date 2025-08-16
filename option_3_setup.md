# Option 3: Azure SQL + Zip Deploy

Use Azure SQL for both APIs; deploy code as Zip with Python runtime.

## Prereqs
- Complete Azure_setup.md sections 0-3 (Azure SQL created)
- Open firewall to your client IP for schema/seed if needed

## 1. Create connection strings
```bash
# URL-encode passwords
export LEAVE_DATABASE_URL="mssql+pyodbc://${LEAVE_SQL_ADMIN}:$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('${LEAVE_SQL_PASSWORD}'))")@${LEAVE_SQL_SERVER}.database.windows.net:1433/${LEAVE_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
export TIMESHEET_DATABASE_URL="mssql+pyodbc://${TIMESHEET_SQL_ADMIN}:$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('${TIMESHEET_SQL_PASSWORD}'))")@${TIMESHEET_SQL_SERVER}.database.windows.net:1433/${TIMESHEET_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
```

## 2. Initialize schema and seed
Use Azure Portal query editor or sqlcmd to run:
- `leave_app/sql/schema.sql`, then `leave_app/sql/seed.sql`
- `timesheet_app/sql/schema.sql`, then `timesheet_app/sql/seed.sql`

## 3. App settings
```bash
az webapp config appsettings set -g "$RG" -n "$LEAVE_API_APP" --settings \
  LEAVE_DB_PROVIDER="mssql" \
  LEAVE_DATABASE_URL="$LEAVE_DATABASE_URL" \
  WEBSITES_PORT="8001"

az webapp config appsettings set -g "$RG" -n "$TIMESHEET_API_APP" --settings \
  TIMESHEET_DB_PROVIDER="mssql" \
  TIMESHEET_DATABASE_URL="$TIMESHEET_DATABASE_URL" \
  WEBSITES_PORT="8002"
```

## 4. Deploy (Zip)
```bash
zip -r leave_api.zip leave_app requirements.txt oryx.ini
az webapp deploy -g "$RG" -n "$LEAVE_API_APP" --src-path leave_api.zip --type zip

zip -r timesheet_api.zip timesheet_app requirements.txt oryx.ini
az webapp deploy -g "$RG" -n "$TIMESHEET_API_APP" --src-path timesheet_api.zip --type zip
```

## 5. Startup command
```bash
az webapp config set -g "$RG" -n "$LEAVE_API_APP" --startup-file "python -m leave_app.startup"
az webapp config set -g "$RG" -n "$TIMESHEET_API_APP" --startup-file "python -m timesheet_app.startup"
```

## 6. Verify health endpoints
