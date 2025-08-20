#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SITE_PACKAGES="/home/site/wwwroot/.python_packages/lib/site-packages"

export PYTHONUNBUFFERED=1
export PATH="$HOME/.local/bin:$PATH"

echo "[startup] Installing dependencies to ${SITE_PACKAGES}..."
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install -r "$ROOT_DIR/requirements.txt" -t "$SITE_PACKAGES"

export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
PORT="${PORT:-8080}"
echo "[startup] Starting app on port ${PORT}"
exec python3 "$ROOT_DIR/startup.py"
