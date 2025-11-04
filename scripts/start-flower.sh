#!/bin/bash

# Get the project root directory
PROJECT_ROOT="$(dirname "$0")/.."
cd "$PROJECT_ROOT"

# Activate the virtual environment
source "be/venv/bin/activate"

# Change to backend directory for Celery commands
cd be

# Start Flower monitoring
echo "Starting Flower monitoring on http://localhost:5555"
celery -A app.celery_app flower --port=5555