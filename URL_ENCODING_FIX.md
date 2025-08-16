# URL Encoding Issues and Fixes

## Problem Summa3. **`test_leave_azure_sql.py`**: New test script specifically for the Leave API Azure SQL connection
4. **`diagnose_azure_sql.py`**: Enhanced diagnostic tool that supports both leave and timesheet databases
5. **`test_sqlalchemy.py`**: SQLAlchemy-specific test tool

The original Azure SQL connection strings in `Azure_setup.md` were not properly URL-encoding passwords that contain special characters. This caused connection timeout errors with passwords like `CHANGE_ME_str0ngP@ss!` because:

1. **`@` character**: Used as a delimiter between credentials and server in URLs, causing the password to be truncated at the `@` symbol
2. **`!` character**: Can cause parsing issues in connection strings and shell environments

## What Was Broken

### Original (Broken) Connection String Format:
```bash
export TIMESHEET_DATABASE_URL="mssql+pyodbc://${TIMESHEET_SQL_ADMIN}:${TIMESHEET_SQL_PASSWORD}@${TIMESHEET_SQL_SERVER}.database.windows.net:1433/${TIMESHEET_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
```

With `TIMESHEET_SQL_PASSWORD="CHANGE_ME_str0ngP@ss!"`, this became:
```
mssql+pyodbc://sqladminuser:CHANGE_ME_str0ngP@ss!@timesheet-sql-server.database.windows.net:1433/timesheet_db...
```

The URL parser sees this as:
- Username: `sqladminuser`
- Password: `CHANGE_ME_str0ngP` (truncated at the first `@`)
- Server: `ss!@timesheet-sql-server.database.windows.net` (incorrect)

## What Was Fixed

### Fixed Connection String Format:
```bash
export TIMESHEET_DATABASE_URL="mssql+pyodbc://${TIMESHEET_SQL_ADMIN}:$(python3 -c "from urllib.parse import quote_plus; print(quote_plus('${TIMESHEET_SQL_PASSWORD}'))")@${TIMESHEET_SQL_SERVER}.database.windows.net:1433/${TIMESHEET_SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&LoginTimeout=30"
```

This properly URL-encodes the password:
- `@` becomes `%40`
- `!` becomes `%21`

So `CHANGE_ME_str0ngP@ss!` becomes `CHANGE_ME_str0ngP%40ss%21`

### Additional Improvements:
1. **Added timeout parameters**: `LoginTimeout=30` to prevent connection timeout errors
2. **Created helper script**: `scripts/generate_connection_strings.sh` for easier connection string generation
3. **Updated test scripts**: `test_azure_sql.py`, `diagnose_azure_sql.py`, and `test_sqlalchemy.py` to handle URL encoding properly

## Files Modified

1. **`Azure_setup.md`**: Fixed connection string examples with proper URL encoding
2. **`test_azure_sql.py`**: Added `quote_plus` import and proper password encoding
3. **`scripts/generate_connection_strings.sh`**: New helper script for generating encoded connection strings
4. **`diagnose_azure_sql.py`**: New diagnostic tool for troubleshooting connection issues
5. **`test_sqlalchemy.py`**: New SQLAlchemy-specific test tool

## Application Code Status

✅ **Both the timesheet API and leave API codebases are correctly implemented**. They simply read their respective environment variables (`TIMESHEET_DATABASE_URL` and `LEAVE_DATABASE_URL`) and pass them to SQLAlchemy. The issue was with how the environment variables were being constructed in the setup documentation, not with the application code.

- `timesheet_app/api/db.py` - ✅ Correctly reads `TIMESHEET_DATABASE_URL`
- `leave_app/api/db.py` - ✅ Correctly reads `LEAVE_DATABASE_URL`

## Testing the Fix

You can verify the fix works for both APIs by running:

**For Timesheet API:**
```bash
cd /home/prwani_u/copilots_code/mcp_demo_app_python
python test_azure_sql.py
```

**For Leave API:**
```bash
cd /home/prwani_u/copilots_code/mcp_demo_app_python
python test_leave_azure_sql.py
```

**Universal Diagnostic Tool:**
```bash
cd /home/prwani_u/copilots_code/mcp_demo_app_python
python diagnose_azure_sql.py
```

Both connections should now succeed without timeout errors.

## Key Takeaway

Always URL-encode passwords and other special characters when constructing database connection strings, especially when using SQLAlchemy with pyodbc drivers for Azure SQL.
