# 🐳 Docker Compose Guide

This guide explains how to run the Dynamic Learning Path AI application using Docker Compose.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **Git** (to clone the repository)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd case-ai-dynamic-learning-path
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API keys
nano .env  # or use your preferred editor
```

**Required API Keys:**
- `OPENAI_API_KEY` - Your OpenAI API key for AI services
- `YOUTUBE_API_KEY` - YouTube Data API key (optional)
- `GOOGLE_BOOKS_API_KEY` - Google Books API key (optional)
- `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` - Spotify API keys (optional)

### 3. Start the Application
```bash
docker compose up --build
```

This command will:
- Build all Docker images
- Start all services (backend, frontend, Redis, Celery workers)
- Create and initialize the database
- Make the app available at:
  - **Frontend**: http://localhost:3000
  - **Backend API**: http://localhost:8001
  - **API Documentation**: http://localhost:8001/docs
  - **Celery Flower (monitoring)**: http://localhost:5555

## 🛑 Stopping the Application

### Stop Services (Keeps Data)
```bash
docker compose down
```

### Stop Services and Remove Volumes (Clean Slate)
```bash
docker compose down -v
```

**⚠️ Warning**: Using `-v` will delete your database and all learning paths!

## 🔄 Development Workflow

### When You Make Code Changes

#### Option 1: Full Rebuild (Recommended)
```bash
# Stop the application
docker compose down

# Rebuild and restart
docker compose up --build
```

#### Option 2: Rebuild Specific Service
```bash
# For backend changes only
docker compose up --build backend

# For frontend changes only
docker compose up --build frontend
```

#### Option 3: Force Rebuild (If Changes Aren't Detected)
```bash
# Stop everything
docker compose down

# Remove old images
docker compose build --no-cache

# Start fresh
docker compose up
```

### Live Development (Without Docker)
For faster development iterations, you can run services locally:

```bash
# Terminal 1: Start Redis and background services
docker compose up redis celery-worker celery-quiz-worker

# Terminal 2: Run backend locally
cd be
python -m uvicorn app.main:app --reload --port 8001

# Terminal 3: Run frontend locally
cd fe
npm run dev
```

## 📊 Monitoring and Logs

### View Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend
docker compose logs celery-quiz-worker

# Follow logs in real-time
docker compose logs -f backend
```

### Monitor Celery Tasks
Visit http://localhost:5555 to see the Celery Flower dashboard for monitoring background tasks.

### Check Service Status
```bash
# List running containers
docker compose ps

# Check health status
docker compose top
```

## 🐛 Troubleshooting

### Common Issues

#### "No such table: modules" Error
**Problem**: Database tables not created
**Solution**:
```bash
docker compose down -v
docker compose up --build
```

#### Port Already in Use
**Problem**: Ports 3000, 8001, 6379, or 5555 are already in use
**Solution**:
```bash
# Find and kill processes using the ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
lsof -ti:6379 | xargs kill -9
lsof -ti:5555 | xargs kill -9

# Or change ports in docker-compose.yml
```

#### Services Won't Start
**Problem**: Docker containers failing to start
**Solution**:
```bash
# Clean everything and start fresh
docker compose down -v
docker system prune -f
docker compose up --build
```

#### Database Connection Issues
**Problem**: Backend can't connect to database
**Solution**:
```bash
# Check if volume mapping is correct
docker compose down
docker volume ls
docker volume prune  # Remove unused volumes
docker compose up --build
```

### Check Service Health
```bash
# Backend health
curl http://localhost:8001/health

# Frontend accessibility
curl http://localhost:3000

# Redis connection
docker compose exec redis redis-cli ping
```

## 🏗️ Architecture Overview

The application consists of these services:

1. **Frontend** (Next.js) - Port 3000
   - User interface
   - Real-time learning path generation

2. **Backend** (FastAPI) - Port 8001
   - REST API
   - Database operations
   - AI service coordination

3. **Redis** - Port 6379
   - Message broker for Celery
   - Task queue management

4. **Celery Workers**
   - `celery-worker`: General tasks
   - `celery-quiz-worker`: Quiz generation
   - `celery-beat`: Scheduled tasks

5. **Flower** - Port 5555
   - Celery monitoring dashboard

## 📁 Data Persistence

### Database
- **Location**: `./be/dlp.db` (SQLite file)
- **Backup**: Copy the `dlp.db` file to backup your data
- **Reset**: Delete `dlp.db` and restart to reset all data

### Vector Database
- **Location**: `./be/chroma_db/`
- **Purpose**: Stores content embeddings for AI search

## 🔧 Configuration

### Environment Variables
Edit `.env` file to configure:
- API keys
- Database URL
- CORS origins
- Log levels

### Docker Compose Customization
Edit `docker-compose.yml` to:
- Change port mappings
- Adjust resource limits
- Modify service configurations

## 📈 Production Deployment

For production deployment, use:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```

This uses the production configuration with:
- Optimized builds
- Production environment settings
- Health checks
- Restart policies

## 🆘 Getting Help

1. **Check logs**: `docker compose logs [service-name]`
2. **Verify environment**: Ensure `.env` file is properly configured
3. **Clean start**: `docker compose down -v && docker compose up --build`
4. **Check ports**: Ensure no other services are using the required ports

## 📝 Development Tips

1. **Use `--build` flag** when you make code changes
2. **Monitor logs** to debug issues
3. **Use Flower** to monitor background tasks
4. **Backup database** before major changes
5. **Clean volumes** if you encounter persistent issues

---

Happy coding! 🚀
