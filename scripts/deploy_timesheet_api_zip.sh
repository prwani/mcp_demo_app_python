#!/usr/bin/env bash
# Deploy Timesheet API (non-Docker) to Azure Web App via Zip Deploy
# Usage:
#   SUFFIX=1234 ./scripts/deploy_timesheet_api_zip.sh
# Optional: KEEP_ZIPS=1 to keep artifacts

set -uo pipefail

if [[ -z "${SUFFIX:-}" ]]; then
  echo "Error: SUFFIX is required (e.g., 1234)" >&2
  echo "Usage: SUFFIX=1234 $0" >&2
  exit 1
fi

RG="mcp-python-demo-rg-${SUFFIX}"
ASP_NAME="mcp-demo-asp-${SUFFIX}"
APP_NAME="mcp-timesheet-api-${SUFFIX}"
KEEP_ZIPS="${KEEP_ZIPS:-1}"

echo "Using SUFFIX: $SUFFIX"
echo "Deploying Timesheet API to RG=$RG, ASP=$ASP_NAME, APP=$APP_NAME"

if ! az account show >/dev/null 2>&1; then
  echo "Please run 'az login' first." >&2
  exit 1
fi

run_cmd() {
  local desc="$1"; shift
  echo "→ ${desc}"
  if "$@" >/dev/null; then
    echo "  ✓ ${desc}"
    return 0
  else
    echo "  ✗ ${desc}"
    return 1
  fi
}

create_app_if_needed() {
  local appname="$1"
  if ! az webapp show -g "$RG" -n "$appname" >/dev/null 2>&1; then
    run_cmd "Create Web App ${appname}" az webapp create -g "$RG" -p "$ASP_NAME" -n "$appname" --runtime "PYTHON|3.10"
  else
    echo "Web App exists: ${appname}"
    return 0
  fi
}

echo "Packaging Timesheet API zip..."
pushd "$(dirname "$0")/.." >/dev/null
ROOT_DIR="$(pwd)"

# Create filtered requirements to avoid pyodbc builds; SQLite default will work
sed '/^\s*pyodbc\b/d' requirements.txt > requirements_api.txt

cd timesheet_app \
  && zip -qr ../timesheet_api.zip . -x "Dockerfile*" "*/__pycache__/*" "*.pyc" "mcp_server/*" \
  && zip -qj ../timesheet_api.zip ../requirements_api.txt \
  && cd ..

if [[ ! -f "timesheet_api.zip" ]]; then
  echo "Error: Failed to create timesheet_api.zip" >&2
  exit 1
fi

ZIP_API="timesheet_api.zip"
popd >/dev/null

if ! unzip -l "$ROOT_DIR/$ZIP_API" >/dev/null 2>&1; then
  echo "Error: Zip file '$ROOT_DIR/$ZIP_API' is invalid or unreadable" >&2
  exit 1
fi

echo "Validating zip contents..."
if ! unzip -l "$ROOT_DIR/$ZIP_API" | awk '{print $4}' | grep -qx "startup.py"; then
  echo "  ✗ Missing startup.py in timesheet_api.zip" >&2
  exit 1
fi
if ! unzip -l "$ROOT_DIR/$ZIP_API" | awk '{print $4}' | grep -qx "requirements_api.txt"; then
  echo "  ✗ Missing requirements_api.txt in timesheet_api.zip" >&2
  exit 1
fi

echo -e "\n=== Deploy: Timesheet API (${APP_NAME}) ==="
ok=true
create_app_if_needed "$APP_NAME" || ok=false

# Disable Oryx build; install at runtime in startup script
run_cmd "Set app settings (Timesheet API)" \
  az webapp config appsettings set -g "$RG" -n "$APP_NAME" --settings \
  WEBSITES_PORT="8002" \
  PORT="8002" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="0" \
  ENABLE_ORYX_BUILD="0" \
  ORYX_PYTHON_VERSION="3.10" \
  PYTHON_VERSION="3.10" \
  DISABLE_COLLECTSTATIC="1" \
  WEBSITE_ENABLE_SYNC_UPDATE_SITE="1" \
  TIMESHEET_DB_PROVIDER="auto" || ok=false

# Use absolute startup path to avoid resolution/exec-bit issues
run_cmd "Set startup (Timesheet API)" \
  az webapp config set -g "$RG" -n "$APP_NAME" --startup-file "bash -c 'chmod +x /home/site/wwwroot/startup_api.sh; /home/site/wwwroot/startup_api.sh'" || ok=false

run_cmd "Zip deploy (Timesheet API)" \
  az webapp deploy -g "$RG" -n "$APP_NAME" --src-path "$ROOT_DIR/$ZIP_API" --type zip || ok=false
if ! $ok; then
  echo "  Falling back to config-zip API..."
  if az webapp deployment source config-zip -g "$RG" -n "$APP_NAME" --src "$ROOT_DIR/$ZIP_API" >/dev/null; then
    echo "  ✓ Fallback config-zip succeeded"
    ok=true
  else
    echo "  ✗ Fallback config-zip failed"
  fi
fi

run_cmd "Restart Timesheet API app" \
  az webapp restart -g "$RG" -n "$APP_NAME" || ok=false

echo -e "\nWaiting 20s for app warmup..."; sleep 20

echo "Testing health..."
if curl -fsS "https://${APP_NAME}.azurewebsites.net/health" >/dev/null; then
  echo "  ✓ Health OK"
else
  echo "  ✗ Health check failed"
fi

echo "Testing OpenAPI JSON..."
if curl -fsS "https://${APP_NAME}.azurewebsites.net/openapi.json" >/dev/null; then
  echo "  ✓ OpenAPI JSON available at /openapi.json"
else
  echo "  ✗ OpenAPI JSON not available yet"
fi

if [[ "$KEEP_ZIPS" == "0" ]]; then
  echo -e "\nCleaning up zip files..."
  rm -f "$ROOT_DIR/$ZIP_API" "$ROOT_DIR/requirements_api.txt"
  echo "✓ Cleanup completed"
else
  echo -e "\nSkipping zip cleanup (KEEP_ZIPS=$KEEP_ZIPS)"
fi

echo -e "\nDone. App: https://${APP_NAME}.azurewebsites.net"
