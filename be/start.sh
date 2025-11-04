#!/bin/bash

# start.sh

# Start the FastAPI application with optimized WebSocket settings
echo "Starting gunicorn server with WebSocket optimizations..."
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8001 \
    --workers 4 \
    --timeout 300 \
    --keep-alive 75 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
