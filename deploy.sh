#!/bin/bash

# Custom deployment script for Azure App Service
set -e

echo "Starting custom deployment..."

# Install Python packages
echo "Installing Python packages from requirements.txt..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Deployment completed successfully!"
