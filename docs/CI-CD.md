# CI/CD Pipeline Documentation

This project uses GitHub Actions for Continuous Integration and Deployment (CI/CD).

## 🚀 Workflows Overview

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**
1. **Backend Testing** - Tests Python FastAPI backend
2. **Frontend Testing** - Tests Next.js frontend
3. **Build & Push** - Builds and pushes Docker images to GitHub Container Registry
4. **Security Scanning** - Scans for vulnerabilities using Trivy
5. **Integration Testing** - Tests the full application stack

### 2. Deploy Pipeline (`.github/workflows/deploy.yml`)

**Triggers:**
- Push to `main` branch
- Version tags (`v*`)

**Features:**
- Deploys to production environment
- Uses production-ready configuration
- Requires manual approval (production environment)

### 3. Dependency Updates (`.github/workflows/dependencies.yml`)

**Triggers:**
- Weekly schedule (Mondays at 9 AM UTC)
- Manual trigger

**Features:**
- Automatically updates Python and Node.js dependencies
- Creates pull requests with dependency updates
- Includes security fixes

## 🔧 Setup Instructions

### 1. Repository Setup

1. **Enable GitHub Actions** in your repository settings
2. **Set up environments** (optional but recommended):
   - Go to Settings → Environments
   - Create `production` environment
   - Add protection rules (require reviewers)

### 2. Container Registry Setup

The CI pipeline automatically publishes Docker images to GitHub Container Registry (ghcr.io).

**Required permissions:**
- Actions have read/write access to packages (enabled by default)

### 3. Secrets Configuration

Add these secrets in your repository settings (Settings → Secrets and variables → Actions):

#### Required for Production Deployment:
```
DATABASE_URL=postgresql://user:password@host:port/database
OPENAI_API_KEY=your_openai_api_key
YOUTUBE_API_KEY=your_youtube_api_key
GOOGLE_BOOKS_API_KEY=your_google_books_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

#### Optional (for advanced deployments):
```
DEPLOY_HOST=your.production.server.com
DEPLOY_USER=ubuntu
DEPLOY_KEY=your_ssh_private_key
```

## 📦 Docker Images

The CI pipeline builds and publishes Docker images with these tags:

**Backend Image:** `ghcr.io/computacenter-ro/case-ai-dynamic-learning-path-backend`
**Frontend Image:** `ghcr.io/computacenter-ro/case-ai-dynamic-learning-path-frontend`

**Tags:**
- `latest` - Latest stable version (main branch)
- `develop` - Development version
- `main-<sha>` - Specific commit from main branch
- `develop-<sha>` - Specific commit from develop branch

## 🔍 Monitoring & Quality

### Code Quality
- **Backend:** Flake8 linting for Python code
- **Frontend:** ESLint for TypeScript/React code
- **Type Checking:** TypeScript compiler checks

### Security
- **Vulnerability Scanning:** Trivy scans dependencies and Docker images
- **SARIF Reports:** Security results uploaded to GitHub Security tab

### Testing
- **Unit Tests:** Backend API tests
- **Integration Tests:** Full stack testing with Docker Compose
- **Build Tests:** Ensures applications build successfully

## 🚀 Deployment Process

### Automatic Deployment (Main Branch)
1. Push to `main` branch triggers deployment
2. All tests must pass
3. Docker images are built and pushed
4. Production deployment workflow runs

### Manual Deployment
1. Go to Actions tab in GitHub
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Choose branch/tag to deploy

### Production Configuration

Use `docker-compose.prod.yml` for production deployments:

```bash
# Pull latest images and deploy
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop services
docker compose -f docker-compose.prod.yml down
```

### Local Development

For local development, use the standard docker-compose command:

```bash
# Development (uses docker-compose.yml)
docker compose up -d

# This automatically:
# - Loads .env files if they exist
# - Uses localhost URLs for API communication
# - Enables development-friendly settings
```

## 🐳 Docker Compose Configurations

The project uses a simplified Docker Compose setup:

### **docker-compose.yml** (Main Configuration)
- Base services configuration for all environments
- Uses environment variables with sensible defaults
- Works with or without .env files
- Supports both development and CI/CD use cases

### **docker-compose.prod.yml** (Production Override)
- Production-ready configuration
- Uses published Docker images from registry
- Optimized for production deployment
- Environment variables from secrets/configuration

## 🔧 Local Development

### Running CI Checks Locally

**Backend:**
```bash
cd be
pip install -r requirements.txt
pip install flake8 pytest

# Linting
flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics

# Tests
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd fe
npm install

# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Build
npm run build
```

**Full Stack:**
```bash
# Start all services
docker compose up -d

# Run integration tests
curl http://localhost:8001/docs
curl http://localhost:3000
```

## 📊 Status Badges

Add these badges to your main README:

```markdown
[![CI Pipeline](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/ci.yml/badge.svg)](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/ci.yml)
[![Deploy](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/deploy.yml/badge.svg)](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/deploy.yml)
```

## 🛠 Troubleshooting

### Common Issues

1. **Docker build fails:**
   - Check Dockerfile syntax
   - Ensure all required files are present
   - Check .dockerignore files

2. **Tests fail:**
   - Check environment variables
   - Ensure test database is properly configured
   - Review test logs in Actions tab

3. **Deployment fails:**
   - Verify all secrets are configured
   - Check production environment settings
   - Review deployment logs

### Getting Help

1. Check the Actions tab for detailed logs
2. Review the "Checks" section in pull requests
3. Check the Security tab for vulnerability reports

## 🔄 Continuous Improvement

### Adding New Tests
1. Add test files to `be/tests/` or `fe/tests/`
2. Update CI workflow if needed
3. Ensure tests run in CI environment

### Updating Dependencies
- Dependency updates are automated weekly
- Review and merge dependency update PRs
- Monitor for breaking changes

### Enhancing Security
- Regular vulnerability scans run automatically
- Review security advisories in GitHub Security tab
- Keep base Docker images updated
