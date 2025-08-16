#!/usr/bin/env bash
# Safer bash settings but allow per-step error handling to continue across components
set -uo pipefail

# Deploy Leave MCP, Timesheet MCP, and Chat Client via Zip Deploy to Azure Web Apps
# Usage:
#   SUFFIX=7859 REGION=eastus2 ./scripts/deploy_mcp_zip.sh
#
# Optional (will be set if present): AOAI_ENDPOINT, AOAI_KEY, AOAI_API_VERSION, AOAI_DEPLOYMENT

if [[ -z "${SUFFIX:-}" ]]; then
  echo "Error: SUFFIX is required (e.g., 7859)" >&2
  echo "Usage: SUFFIX=7859 $0" >&2
  exit 1
fi

echo "Using SUFFIX: $SUFFIX"

RG="mcp-python-demo-rg-${SUFFIX}"
ASP_NAME="mcp-demo-asp-${SUFFIX}"
LEAVE_API_APP="mcp-leave-api-${SUFFIX}"
TIMESHEET_API_APP="mcp-timesheet-api-${SUFFIX}"
LEAVE_MCP_APP="mcp-leave-mcp-${SUFFIX}"
TIMESHEET_MCP_APP="mcp-timesheet-mcp-${SUFFIX}"
CHAT_CLIENT_APP="mcp-chat-client-${SUFFIX}"

echo "Deploying to Resource Group: ${RG}"

# Ensure az is logged in
if ! az account show >/dev/null 2>&1; then
  echo "Please run 'az login' first." >&2
  exit 1
fi

# Which components to deploy
# You can use ONLY_LEAVE=1 to deploy only Leave MCP, or set DO_LEAVE/DO_TIMESHEET/DO_CHAT explicitly
DO_LEAVE="${DO_LEAVE:-1}"
DO_TIMESHEET="${DO_TIMESHEET:-1}"
DO_CHAT="${DO_CHAT:-1}"
if [[ "${ONLY_LEAVE:-0}" == "1" ]]; then
  DO_LEAVE=1
  DO_TIMESHEET=0
  DO_CHAT=0
  echo "ONLY_LEAVE=1 -> deploying Leave MCP only"
fi

# Keep zip artifacts for investigation by default; set KEEP_ZIPS=0 to clean up
KEEP_ZIPS="${KEEP_ZIPS:-1}"

# Helpers
run_cmd() {
  # Run a command and return 0/1, suppressing set -e behavior
  # Usage: run_cmd <desc> <cmd...>
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

# Build zips once (using same pattern as working APIs)
echo "Packaging zip artifacts..."
pushd "$(dirname "$0")/.." >/dev/null

ROOT_DIR="$(pwd)"

# Create filtered requirements.txt without pyodbc for MCP servers
sed '/^\s*pyodbc\b/d' requirements.txt > requirements_mcp.txt

# Package zips with flattened structure for Azure deployment (excluding unnecessary files)
# Note: Add requirements_mcp.txt using -j to avoid parent path entries in the zip (prevents Kudu 400)
if [[ "$DO_LEAVE" == "1" ]]; then
  cd leave_app \
    && zip -qr ../leave_mcp.zip . -x "Dockerfile*" "*/__pycache__/*" "*.pyc" "web/*" "sql/*" "api/*" \
    && zip -qj ../leave_mcp.zip ../requirements_mcp.txt \
  && bash -lc 'echo skip > ../.oryx' \
  && zip -qj ../leave_mcp.zip ../.oryx \
    && cd ..
  if [[ ! -f "leave_mcp.zip" ]]; then
    echo "Error: Failed to create leave_mcp.zip" >&2
    exit 1
  fi
fi

if [[ "$DO_TIMESHEET" == "1" ]]; then
  cd timesheet_app \
    && zip -qr ../timesheet_mcp.zip . -x "Dockerfile*" "*/__pycache__/*" "*.pyc" "web/*" "sql/*" "api/*" \
  && zip -qj ../timesheet_mcp.zip ../requirements_mcp.txt \
  && bash -lc 'echo skip > ../.oryx' \
  && zip -qj ../timesheet_mcp.zip ../.oryx \
    && cd ..
  if [[ ! -f "timesheet_mcp.zip" ]]; then
    echo "Error: Failed to create timesheet_mcp.zip" >&2
    exit 1
  fi
fi

if [[ "$DO_CHAT" == "1" ]]; then
  cd chat_client \
    && zip -qr ../chat_client.zip . -x "Dockerfile*" "*/__pycache__/*" "*.pyc" \
    && zip -qj ../chat_client.zip ../requirements_mcp.txt \
    && cd ..
  if [[ ! -f "chat_client.zip" ]]; then
    echo "Error: Failed to create chat_client.zip" >&2
    exit 1
  fi
fi

echo "✓ All zip files created successfully (including startup.sh files)"

ZIP_LEAVE_MCP="leave_mcp.zip"
ZIP_TIMESHEET_MCP="timesheet_mcp.zip"
ZIP_CHAT="chat_client.zip"

ROOT_ZIP_DIR="$ROOT_DIR"
popd >/dev/null

# Quick sanity checks: ensure required files are present at zip root
if [[ "$DO_LEAVE" == "1" ]]; then
  if ! unzip -l "$ROOT_DIR/$ZIP_LEAVE_MCP" >/dev/null 2>&1; then
    echo "Error: Zip file '$ROOT_DIR/$ZIP_LEAVE_MCP' is invalid or unreadable" >&2
    exit 1
  fi
fi
if [[ "$DO_TIMESHEET" == "1" ]]; then
  if ! unzip -l "$ROOT_DIR/$ZIP_TIMESHEET_MCP" >/dev/null 2>&1; then
    echo "Error: Zip file '$ROOT_DIR/$ZIP_TIMESHEET_MCP' is invalid or unreadable" >&2
    exit 1
  fi
fi
if [[ "$DO_CHAT" == "1" ]]; then
  if ! unzip -l "$ROOT_DIR/$ZIP_CHAT" >/dev/null 2>&1; then
    echo "Error: Zip file '$ROOT_DIR/$ZIP_CHAT' is invalid or unreadable" >&2
    exit 1
  fi
fi

check_in_zip() {
  local zip_file="$1"; shift
  local missing=0
  for f in "$@"; do
    if ! unzip -l "$zip_file" | awk '{print $4}' | grep -qx "$f"; then
      echo "  ✗ Missing '$f' in $(basename "$zip_file")" >&2
      missing=1
    fi
  done
  return $missing
}

echo "Validating zip contents..."
if [[ "$DO_LEAVE" == "1" ]]; then
  check_in_zip "$ROOT_DIR/$ZIP_LEAVE_MCP" startup.sh startup_mcp.py requirements_mcp.txt || {
    echo "Error: leave_mcp.zip is missing required files (startup.sh/startup_mcp.py/requirements_mcp.txt)" >&2
    exit 1
  }
fi
if [[ "$DO_TIMESHEET" == "1" ]]; then
  check_in_zip "$ROOT_DIR/$ZIP_TIMESHEET_MCP" startup.sh startup_mcp.py requirements_mcp.txt || {
    echo "Error: timesheet_mcp.zip is missing required files (startup.sh/startup_mcp.py/requirements_mcp.txt)" >&2
    exit 1
  }
fi
if [[ "$DO_CHAT" == "1" ]]; then
  check_in_zip "$ROOT_DIR/$ZIP_CHAT" startup.sh requirements_mcp.txt || {
    echo "Warning: chat_client.zip missing expected files; continuing" >&2
  }
fi

# Track results
declare -A RESULTS
if [[ "$DO_LEAVE" == "1" ]]; then RESULTS[leave_mcp]="FAILED"; else RESULTS[leave_mcp]="SKIPPED"; fi
if [[ "$DO_TIMESHEET" == "1" ]]; then RESULTS[timesheet_mcp]="FAILED"; else RESULTS[timesheet_mcp]="SKIPPED"; fi
if [[ "$DO_CHAT" == "1" ]]; then RESULTS[chat_client]="FAILED"; else RESULTS[chat_client]="SKIPPED"; fi

# Deploy Leave MCP
if [[ "$DO_LEAVE" == "1" ]]; then
  echo -e "\n=== Deploy: Leave MCP (${LEAVE_MCP_APP}) ==="
  leave_ok=true
  create_app_if_needed "$LEAVE_MCP_APP" || leave_ok=false
  run_cmd "Set app settings (Leave MCP)" \
    az webapp config appsettings set -g "$RG" -n "$LEAVE_MCP_APP" --settings \
    LEAVE_API_URL="https://${LEAVE_API_APP}.azurewebsites.net" \
    WEBSITES_PORT="8011" \
    PORT="8011" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="0" \
  ENABLE_ORYX_BUILD="0" \
    ORYX_PYTHON_VERSION="3.10" \
    PYTHON_VERSION="3.10" \
    DISABLE_COLLECTSTATIC="1" \
    WEBSITE_ENABLE_SYNC_UPDATE_SITE="1" || leave_ok=false
  run_cmd "Set startup (Leave MCP)" \
    az webapp config set -g "$RG" -n "$LEAVE_MCP_APP" --startup-file "bash -c 'chmod +x /home/site/wwwroot/startup.sh; /home/site/wwwroot/startup.sh'" || leave_ok=false
  run_cmd "Zip deploy (Leave MCP)" \
    az webapp deploy -g "$RG" -n "$LEAVE_MCP_APP" --src-path "$ROOT_ZIP_DIR/$ZIP_LEAVE_MCP" --type zip || leave_ok=false
  if ! $leave_ok; then
    echo "  Falling back to config-zip API..."
    # Older API sometimes bypasses transient 400s from 'az webapp deploy'
    if az webapp deployment source config-zip -g "$RG" -n "$LEAVE_MCP_APP" --src "$ROOT_ZIP_DIR/$ZIP_LEAVE_MCP" >/dev/null; then
      echo "  ✓ Fallback config-zip succeeded"
      leave_ok=true
    else
      echo "  ✗ Fallback config-zip failed"
    fi
  fi
  run_cmd "Restart Leave MCP app" \
    az webapp restart -g "$RG" -n "$LEAVE_MCP_APP" || leave_ok=false
  if $leave_ok; then RESULTS[leave_mcp]="SUCCEEDED"; fi

  echo "  Waiting 10s to avoid SCM restart conflicts..."
  sleep 10
else
  echo -e "\n=== Deploy: Leave MCP (${LEAVE_MCP_APP}) SKIPPED ==="
fi

if [[ "$DO_TIMESHEET" == "1" ]]; then
  echo -e "\n=== Deploy: Timesheet MCP (${TIMESHEET_MCP_APP}) ==="
  echo "  Waiting 30s between components to avoid conflicts..."
  sleep 30
  timesheet_ok=true
  create_app_if_needed "$TIMESHEET_MCP_APP" || timesheet_ok=false
  run_cmd "Set app settings (Timesheet MCP)" \
    az webapp config appsettings set -g "$RG" -n "$TIMESHEET_MCP_APP" --settings \
    TIMESHEET_API_URL="https://${TIMESHEET_API_APP}.azurewebsites.net" \
    WEBSITES_PORT="8012" \
    PORT="8012" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="0" \
  ENABLE_ORYX_BUILD="0" \
    ORYX_PYTHON_VERSION="3.10" \
    PYTHON_VERSION="3.10" \
    DISABLE_COLLECTSTATIC="1" \
    WEBSITE_ENABLE_SYNC_UPDATE_SITE="1" || timesheet_ok=false
  run_cmd "Set startup (Timesheet MCP)" \
    az webapp config set -g "$RG" -n "$TIMESHEET_MCP_APP" --startup-file "bash -c 'chmod +x /home/site/wwwroot/startup.sh; /home/site/wwwroot/startup.sh'" || timesheet_ok=false
  run_cmd "Zip deploy (Timesheet MCP)" \
    az webapp deploy -g "$RG" -n "$TIMESHEET_MCP_APP" --src-path "$ROOT_ZIP_DIR/$ZIP_TIMESHEET_MCP" --type zip || timesheet_ok=false
  if ! $timesheet_ok; then
    echo "  Falling back to config-zip API..."
    if az webapp deployment source config-zip -g "$RG" -n "$TIMESHEET_MCP_APP" --src "$ROOT_ZIP_DIR/$ZIP_TIMESHEET_MCP" >/dev/null; then
      echo "  ✓ Fallback config-zip succeeded"
      timesheet_ok=true
    else
      echo "  ✗ Fallback config-zip failed"
    fi
  fi
  run_cmd "Restart Timesheet MCP app" \
    az webapp restart -g "$RG" -n "$TIMESHEET_MCP_APP" || timesheet_ok=false
  if $timesheet_ok; then RESULTS[timesheet_mcp]="SUCCEEDED"; fi
else
  echo -e "\n=== Deploy: Timesheet MCP (${TIMESHEET_MCP_APP}) SKIPPED ==="
fi

echo "  Waiting 10s to avoid SCM restart conflicts..."
sleep 10

if [[ "$DO_CHAT" == "1" ]]; then
  echo -e "\n=== Deploy: MCP Chat Client (${CHAT_CLIENT_APP}) ==="
  echo "  Waiting 30s between components to avoid conflicts..."
  sleep 30
  chat_ok=true
  create_app_if_needed "$CHAT_CLIENT_APP" || chat_ok=false

  CHAT_SETTINGS=(
    "LEAVE_MCP_URL=https://${LEAVE_MCP_APP}.azurewebsites.net"
    "TIMESHEET_MCP_URL=https://${TIMESHEET_MCP_APP}.azurewebsites.net"
    "WEBSITES_PORT=8000"
    "PORT=8000"
  )
  if [[ -n "${AOAI_ENDPOINT:-}" ]]; then CHAT_SETTINGS+=("AZURE_OPENAI_ENDPOINT=${AOAI_ENDPOINT}"); fi
  if [[ -n "${AOAI_KEY:-}" ]]; then CHAT_SETTINGS+=("AZURE_OPENAI_KEY=${AOAI_KEY}"); fi
  if [[ -n "${AOAI_API_VERSION:-}" ]]; then CHAT_SETTINGS+=("AZURE_OPENAI_API_VERSION=${AOAI_API_VERSION}"); fi
  if [[ -n "${AOAI_DEPLOYMENT:-}" ]]; then CHAT_SETTINGS+=("AZURE_OPENAI_DEPLOYMENT=${AOAI_DEPLOYMENT}"); fi

  run_cmd "Set app settings (Chat Client)" \
    az webapp config appsettings set -g "$RG" -n "$CHAT_CLIENT_APP" --settings "${CHAT_SETTINGS[@]}" || chat_ok=false
  # Ensure Oryx build flags on Chat Client too
  run_cmd "Enable Oryx build (Chat Client)" \
    az webapp config appsettings set -g "$RG" -n "$CHAT_CLIENT_APP" --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT="0" \
  ENABLE_ORYX_BUILD="0" \
    ORYX_PYTHON_VERSION="3.10" \
    PYTHON_VERSION="3.10" \
    DISABLE_COLLECTSTATIC="1" \
    WEBSITE_ENABLE_SYNC_UPDATE_SITE="1" || chat_ok=false
  run_cmd "Set startup (Chat Client)" \
    az webapp config set -g "$RG" -n "$CHAT_CLIENT_APP" --startup-file "bash -c 'chmod +x /home/site/wwwroot/startup.sh; /home/site/wwwroot/startup.sh'" || chat_ok=false
  run_cmd "Zip deploy (Chat Client)" \
    az webapp deploy -g "$RG" -n "$CHAT_CLIENT_APP" --src-path "$ROOT_ZIP_DIR/$ZIP_CHAT" --type zip || chat_ok=false
  if ! $chat_ok; then
    echo "  Falling back to config-zip API..."
    if az webapp deployment source config-zip -g "$RG" -n "$CHAT_CLIENT_APP" --src "$ROOT_ZIP_DIR/$ZIP_CHAT" >/dev/null; then
      echo "  ✓ Fallback config-zip succeeded"
      chat_ok=true
    else
      echo "  ✗ Fallback config-zip failed"
    fi
  fi
  run_cmd "Restart Chat Client app" \
    az webapp restart -g "$RG" -n "$CHAT_CLIENT_APP" || chat_ok=false
  if $chat_ok; then RESULTS[chat_client]="SUCCEEDED"; fi
else
  echo -e "\n=== Deploy: MCP Chat Client (${CHAT_CLIENT_APP}) SKIPPED ==="
fi

echo -e "\n=== Deployment Summary ==="
printf "%-18s : %s\n" "Leave MCP" "${RESULTS[leave_mcp]}"
printf "%-18s : %s\n" "Timesheet MCP" "${RESULTS[timesheet_mcp]}"
printf "%-18s : %s\n" "MCP Chat Client" "${RESULTS[chat_client]}"

echo -e "\nEndpoints:"
echo "  Leave MCP:      https://${LEAVE_MCP_APP}.azurewebsites.net/mcp/health"
echo "  Timesheet MCP:  https://${TIMESHEET_MCP_APP}.azurewebsites.net/mcp/health"
echo "  Chat Client:    https://${CHAT_CLIENT_APP}.azurewebsites.net/health (UI at /)"

echo -e "\nTesting endpoints (waiting 30s for startup)..."
sleep 30

# Test endpoints
echo "Testing Leave MCP health..."
if curl -s "https://${LEAVE_MCP_APP}.azurewebsites.net/mcp/health" >/dev/null 2>&1; then
  echo "  ✓ Leave MCP is responding"
else
  echo "  ✗ Leave MCP is not responding yet"
fi

echo "Testing Timesheet MCP health..."
if curl -s "https://${TIMESHEET_MCP_APP}.azurewebsites.net/mcp/health" >/dev/null 2>&1; then
  echo "  ✓ Timesheet MCP is responding"
else
  echo "  ✗ Timesheet MCP is not responding yet"
fi

echo "Testing Chat Client health..."
if curl -s "https://${CHAT_CLIENT_APP}.azurewebsites.net/health" >/dev/null 2>&1; then
  echo "  ✓ Chat Client is responding"
else
  echo "  ✗ Chat Client is not responding yet"
fi

# Cleanup zip files (optional)
if [[ "$KEEP_ZIPS" == "0" ]]; then
  echo -e "\nCleaning up zip files..."
  rm -f leave_mcp.zip timesheet_mcp.zip chat_client.zip requirements_mcp.txt
  echo "✓ Cleanup completed"
else
  echo -e "\nSkipping zip cleanup (KEEP_ZIPS=$KEEP_ZIPS)"
fi
