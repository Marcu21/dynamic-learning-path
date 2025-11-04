#!/bin/bash

# Quick Setup Script for Dynamic Learning Path AI Application
# This script helps you get started quickly with the application

set -e

echo "🚀 Setting up Dynamic Learning Path AI Application..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for docker compose (modern) or docker-compose (legacy)
DOCKER_COMPOSE_CMD=""
if command_exists "docker" && docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "✅ Docker with compose plugin is available"
elif command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "✅ Docker and docker-compose are available"
else
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if environment files exist
echo ""
echo "🔧 Checking environment configuration..."

if [ ! -f "be/.env" ]; then
    echo "📝 Creating backend environment file..."
    cp .env.example be/.env
    echo "⚠️  Please edit be/.env with your API keys and configuration"
    ENV_NEEDS_CONFIG=true
fi

if [ ! -f "fe/.env.local" ]; then
    echo "📝 Creating frontend environment file..."
    cp .env.example fe/.env.local
    echo "⚠️  Please edit fe/.env.local with your configuration"
    ENV_NEEDS_CONFIG=true
fi

# Install dependencies if running locally
echo ""
echo "📦 Setting up dependencies..."

if command_exists node && command_exists npm; then
    echo "📱 Installing frontend dependencies..."
    cd fe
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
else
    echo "⚠️  Node.js/npm not found - skipping frontend dependency installation"
fi

if command_exists python3; then
    echo "🐍 Installing backend dependencies..."
    cd be
    python3 -m pip install -r requirements.txt
    cd ..
    echo "✅ Backend dependencies installed"
else
    echo "⚠️  Python not found - skipping backend dependency installation"
fi

# Build and start services
echo ""
echo "🐳 Building and starting services with Docker..."

# Stop any existing containers
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Build and start
$DOCKER_COMPOSE_CMD up -d --build

echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "🔍 Checking service health..."

# Check backend
if curl -s -f http://localhost:8001/docs > /dev/null; then
    echo "✅ Backend is running at http://localhost:8001"
    echo "📖 API Documentation: http://localhost:8001/docs"
else
    echo "❌ Backend is not responding"
    echo "📋 Check logs with: $DOCKER_COMPOSE_CMD logs backend"
fi

# Check frontend
if curl -s -f http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "❌ Frontend is not responding"
    echo "📋 Check logs with: $DOCKER_COMPOSE_CMD logs frontend"
fi

# Show next steps
echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. 🌐 Open http://localhost:3000 to access the application"
echo "2. 📖 View API docs at http://localhost:8001/docs"
echo "3. 📝 Configure your API keys in be/.env if needed"
echo "4. 🔧 Check logs with: $DOCKER_COMPOSE_CMD logs -f"
echo "5. 🛑 Stop services with: $DOCKER_COMPOSE_CMD down"

if [ "${ENV_NEEDS_CONFIG:-false}" = true ]; then
    echo ""
    echo "⚠️  IMPORTANT: You need to configure your environment files with valid API keys!"
    echo "   Edit be/.env and add your OpenAI, YouTube, Google Books, and Spotify API keys"
    echo "   Then restart with: $DOCKER_COMPOSE_CMD restart"
fi

echo ""
echo "📚 For more information, check:"
echo "   - README.md for detailed documentation"
echo "   - docs/CI-CD.md for CI/CD pipeline information"
echo "   - Run ./scripts/check-cicd.sh to verify CI/CD setup"

echo ""
echo "🚀 Happy learning!"
