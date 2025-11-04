#!/bin/bash

# Get the project root directory
PROJECT_ROOT="$(dirname "$0")/.."
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate the virtual environment
source "be/venv/bin/activate"

# Change to backend directory for Celery commands
cd be

# Start Celery worker for path generation, quiz generation, and module insertion
celery -A app.celery_app worker --loglevel=info --concurrency=1 --pool=solo --queues=path_generation,quiz_generation,module_insertion --hostname=path-worker@%h > ../logs/celery_path_worker.log 2>&1 &

# Start Celery worker for chat assistant
celery -A app.celery_app worker --loglevel=info --concurrency=2 --pool=solo --queues=chat_assistant --hostname=chat-worker@%h > ../logs/celery_chat_worker.log 2>&1 &

# Print status
sleep 2
echo "All Celery workers started!"
echo ""
echo "Workers:"
echo "- Path Generation Worker (path_generation, quiz_generation, module_insertion queues)"
echo "- Chat Assistant Worker (chat_assistant queue)"
echo ""
echo "Check logs/celery_path_worker.log and logs/celery_chat_worker.log for logs."