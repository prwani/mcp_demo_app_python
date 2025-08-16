#!/usr/bin/env bash
set -e

echo "Starting Timesheet API startup script..."

cd /home/site/wwwroot

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements_api.txt

echo "Starting Timesheet API..."
python startup.py
