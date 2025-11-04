#!/bin/bash

# GitHub Actions Status Check Script
# This script helps verify that CI/CD is set up correctly

set -e

echo "🔍 Checking CI/CD Setup..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check if .github/workflows directory exists
if [ ! -d ".github/workflows" ]; then
    echo "❌ .github/workflows directory not found"
    exit 1
fi

echo "✅ Found .github/workflows directory"

# Check for workflow files
WORKFLOWS=("ci.yml" "deploy.yml" "dependencies.yml")
for workflow in "${WORKFLOWS[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        echo "✅ Found $workflow"
    else
        echo "❌ Missing $workflow"
    fi
done

# Check Docker files
echo ""
echo "🐳 Checking Docker configuration..."

if [ -f "docker-compose.yml" ]; then
    echo "✅ Found docker-compose.yml"
else
    echo "❌ Missing docker-compose.yml"
fi

if [ -f "docker-compose.prod.yml" ]; then
    echo "✅ Found docker-compose.prod.yml"
else
    echo "❌ Missing docker-compose.prod.yml"
fi

# Check Docker Compose availability
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "✅ Docker with compose plugin available"
elif command -v docker-compose >/dev/null 2>&1; then
    echo "✅ Docker-compose (legacy) available"
else
    echo "⚠️  Docker Compose not available (may affect local development)"
fi

if [ -f "be/Dockerfile" ]; then
    echo "✅ Found backend Dockerfile"
else
    echo "❌ Missing backend Dockerfile"
fi

if [ -f "fe/Dockerfile" ]; then
    echo "✅ Found frontend Dockerfile"
else
    echo "❌ Missing frontend Dockerfile"
fi

# Check test files
echo ""
echo "🧪 Checking test configuration..."

if [ -d "be/tests" ]; then
    echo "✅ Found backend tests directory"
else
    echo "❌ Missing backend tests directory"
fi

if [ -f "fe/.eslintrc.json" ]; then
    echo "✅ Found frontend ESLint configuration"
else
    echo "❌ Missing frontend ESLint configuration"
fi

# Check for environment files
echo ""
echo "🔧 Checking environment configuration..."

if [ -f ".env.example" ]; then
    echo "✅ Found unified environment configuration (.env.example)"
else
    echo "⚠️  Consider adding .env.example for environment variables"
fi

if [ -f "be/.env" ]; then
    echo "✅ Found backend environment configuration (be/.env)"
else
    echo "⚠️  Backend .env not found (will be generated from .env.example)"
fi

if [ -f "fe/.env.local" ]; then
    echo "✅ Found frontend environment configuration (fe/.env.local)"
else
    echo "⚠️  Frontend .env.local not found (will be generated from .env.example)"
fi

# Check remote repository
echo ""
echo "🌐 Checking remote repository..."

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -n "$REMOTE_URL" ]; then
    echo "✅ Remote repository: $REMOTE_URL"
    
    if [[ "$REMOTE_URL" == *"github.com"* ]]; then
        echo "✅ GitHub repository detected"
    else
        echo "⚠️  Not a GitHub repository - GitHub Actions may not work"
    fi
else
    echo "❌ No remote repository configured"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Commit and push your changes to trigger the CI pipeline"
echo "2. Check the Actions tab in your GitHub repository"
echo "3. Configure repository secrets for production deployment"
echo "4. Set up GitHub environments for additional protection"

echo ""
echo "🎉 CI/CD setup check complete!"
