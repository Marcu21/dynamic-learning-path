@echo off
REM Activate the virtual environment
cd /d "%~dp0..\be"

REM Start Celery workers with optimized configurations for different task types

REM Worker 1: Path generation tasks
start "Path Generation Worker" cmd /k "celery -A app.celery_app worker --loglevel=info --concurrency=1 --pool=solo --queues=path_generation,quiz_generation,module_insertion --hostname=path-worker@%%h"

REM Worker 2: Chat assistant tasks
start "Chat Assistant Worker" cmd /k "celery -A app.celery_app worker --loglevel=info --concurrency=2 --pool=solo --queues=chat_assistant --hostname=chat-worker@%%h"

echo All Celery workers started!
echo.
echo Workers:
echo - Path Generation Worker (path_generation, quiz_generation queues)
echo - Chat Assistant Worker (chat_assistant queue)
echo.
echo Press any key to continue...
pause >nul