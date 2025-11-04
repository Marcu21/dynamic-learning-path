#!/bin/bash

echo "Stopping Celery workers..."

# Kill all celery worker processes
pkill -f "celery.*worker"

# Wait a moment for graceful shutdown
sleep 2

# Force kill if any are still running
pkill -9 -f "celery.*worker" 2>/dev/null

echo "Celery workers stopped."
