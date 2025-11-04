# 🚀 Quick Start Guide: Using Your CI/CD Pipeline

## What Just Happened? ✨

You now have a fully automated CI/CD pipeline! Here's what you need to know:

## 🎯 Step-by-Step Usage

### 1. **Check Your Pipeline Status**

Go to your GitHub repository and click the **"Actions"** tab:
```
https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions
```

You should see your workflows running or completed.

### 2. **Configure Repository Secrets** (Required for Production)

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

```bash
# Required API Keys
OPENAI_API_KEY=your_actual_openai_key
YOUTUBE_API_KEY=your_actual_youtube_key
GOOGLE_BOOKS_API_KEY=your_actual_google_books_key
SPOTIFY_CLIENT_ID=your_actual_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_actual_spotify_client_secret

# Database (for production)
DATABASE_URL=postgresql://user:password@host:port/database
```

### 3. **How the Pipeline Works**

#### **On Every Push/PR:**
- ✅ **Tests** your backend and frontend code
- ✅ **Lints** code for quality issues
- ✅ **Scans** for security vulnerabilities
- ✅ **Builds** Docker images
- ✅ **Runs** integration tests

#### **On Push to Main Branch:**
- ✅ All the above, PLUS
- ✅ **Publishes** Docker images to GitHub Container Registry
- ✅ **Triggers** production deployment

## 🔄 Daily Development Workflow

### **Making Changes:**
```bash
# 1. Create a feature branch
git checkout -b feature/my-awesome-feature

# 2. Make your changes
# ... edit files ...

# 3. Commit and push
git add .
git commit -m "feat: add awesome feature"
git push origin feature/my-awesome-feature
```

### **What Happens Next:**
1. **CI Pipeline Runs** - Tests, builds, scans for security issues
2. **Review Results** - Check the Actions tab for any failures
3. **Create Pull Request** - When ready, create PR to main
4. **Automatic Deployment** - When PR is merged to main, deploys automatically

## 📊 Monitoring Your Pipeline

### **Check Pipeline Status:**
```bash
# Option 1: GitHub Web Interface
# Go to: https://github.com/your-repo/actions

# Option 2: Command Line (optional)
gh workflow list
gh run list
```

### **View Logs:**
- Click on any workflow run in the Actions tab
- Click on individual jobs to see detailed logs
- Red ❌ means failure, Green ✅ means success

## 🛠 Local Development

### **Before Pushing:**
```bash
# Test locally first
./scripts/setup.sh

# Check CI/CD setup
./scripts/check-cicd.sh

# Run tests manually
cd be && python -m pytest tests/ -v
cd fe && npm run lint && npm run build
```

## 🚀 Deployment Options

### **Automatic Deployment (Recommended):**
- Just push to `main` branch
- Pipeline automatically deploys to production

### **Manual Deployment:**
1. Go to Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Choose branch to deploy

### **Production Environment:**
Your app will be available at:
- **Frontend:** `http://your-server:3000`
- **Backend:** `http://your-server:8001`
- **API Docs:** `http://your-server:8001/docs`

## 🔒 Security & Best Practices

### **What's Protected:**
- ✅ Never commit API keys (use secrets)
- ✅ .env files are in .gitignore and not committed
- ✅ CI creates temporary .env files for validation only
- ✅ Vulnerability scanning on every push
- ✅ Container security scanning
- ✅ Code quality checks

### **Branch Protection (Recommended Setup):**
1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require status checks
   - ✅ Require up-to-date branches
   - ✅ Require review from code owners

## 🔧 Environment Configuration

### **How .env Files Work:**

1. **Local Development:**
   - Create `be/.env` and `fe/.env.local` from the unified `.env.example`
   - Files are loaded automatically by `docker-compose.yml`
   - Never committed to repository (in .gitignore)

2. **CI/CD Pipeline:**
   - Environment variables provided directly in GitHub Actions
   - Uses the same `docker-compose.yml` with explicit environment variables
   - No .env files needed in CI environment

3. **Production:**
   - Environment variables provided via secrets or configuration
   - Uses `docker-compose.prod.yml` with explicit variables
   - No .env files needed in production

### **Setting Up Locally:**
```bash
# Copy the unified environment template
cp .env.example be/.env
cp .env.example fe/.env.local

# Edit with your real API keys
nano be/.env
nano fe/.env.local

# Start development (uses single docker-compose.yml)
docker compose up -d
```

### **Simplified Architecture:**
- **Single docker-compose.yml** - works for all environments
- **Optional .env files** - for local development convenience
- **Environment variables** - with sensible defaults
- **No complex overrides** - easier to understand and maintain

## 📋 Common Commands

```bash
# Start development environment
./scripts/setup.sh

# Check CI/CD status
./scripts/check-cicd.sh

# View running containers
docker compose ps

# View logs
docker compose logs -f

# Stop everything
docker compose down

# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

## 🆘 Troubleshooting

### **Pipeline Fails:**
1. Check the Actions tab for error details
2. Look at the specific job that failed
3. Fix the issue and push again

### **Tests Fail:**
```bash
# Run tests locally
cd be && python -m pytest tests/ -v
cd fe && npm test

# Fix issues and commit
git add .
git commit -m "fix: resolve test issues"
git push
```

### **Docker Issues:**
```bash
# Rebuild containers
docker compose down
docker compose up -d --build

# Check logs
docker compose logs backend
docker compose logs frontend
```

## 🎉 You're Ready!

Your CI/CD pipeline is now active and running! Every time you push code:

1. **Tests run automatically** ✅
2. **Code quality is checked** ✅  
3. **Security is scanned** ✅
4. **Docker images are built** ✅
5. **Production deploys automatically** (on main branch) ✅

**Happy coding! Your pipeline will take care of the rest! 🚀**
