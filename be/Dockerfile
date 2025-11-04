# Dockerfile for FastAPI Backend

# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 3. Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# 4. Set the working directory in the container
WORKDIR /app

# 5. Copy the requirements file into the container at /app
COPY ./requirements.txt /app/requirements.txt

# 6. Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the backend application's source code into the container
COPY . /app

# 8. Create a non-root user
RUN adduser --disabled-password --gecos '' --uid 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 9. Expose the port the app runs on
EXPOSE 8001

# 10. Create a startup script
COPY --chown=appuser:appuser start.sh /app/start.sh
RUN chmod +x /app/start.sh

# 11. Define the command to run the application
CMD ["/app/start.sh"]
