# Dynamic Learning Path AI Application

[![CI Pipeline](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/ci.yml/badge.svg)](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/ci.yml)
[![Deploy](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/deploy.yml/badge.svg)](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/actions/workflows/deploy.yml)

A full-stack AI-powered application that creates personalized learning paths by intelligently searching and curating educational content from multiple platforms.

## 🚀 Features

- **AI-Powered Learning Paths**: Generates personalized learning modules using OpenAI
- **Multi-Platform Content Search**: Integrates with YouTube, Google Books, and Spotify
- **Intelligent Content Ranking**: Uses AI to select the most effective learning materials
- **Progress Tracking**: Monitor learning progress and completion status
- **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- **Real-time Streaming**: Live generation of learning content with progress updates

## 🏗 Architecture

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and Framer Motion
- **Backend**: FastAPI with Python 3.11, SQLAlchemy, and Pydantic
- **AI/ML**: OpenAI GPT models, LangChain, and LangGraph
- **Database**: SQLite (development) / PostgreSQL (production)
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions with automated testing and deployment

## 🛠 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose
- API keys for OpenAI, YouTube, Google Books, and Spotify

### 1. Clone the Repository

```bash
git clone https://github.com/computacenter-ro/case-ai-dynamic-learning-path.git
cd case-ai-dynamic-learning-path
```

### 2. Environment Setup

**Unified Configuration:**
```bash
# Copy the environment template
cp .env.example be/.env
cp .env.example fe/.env.local

# Edit both files with your API keys and configuration
# (The same template works for both backend and frontend)
```

### 3. Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Running Locally (Development)

**Backend:**
```bash
cd be
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
cd fe
npm install
npm run dev
```

## 📱 Usage

1. **Access the Application**: Open http://localhost:3000
2. **Create a User Profile**: Set up your learning preferences and goals
3. **Generate Learning Path**: Describe what you want to learn
4. **Follow the Modules**: Progress through personalized learning content
5. **Track Progress**: Monitor your completion and learning journey

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd be && python -m pytest tests/ -v

# Frontend tests
cd fe && npm test

# Integration tests with Docker
docker-compose up -d
curl http://localhost:8001/docs
curl http://localhost:3000
```

### CI/CD Status Check
```bash
./scripts/check-cicd.sh
```

## 🚀 Deployment

### Automatic Deployment
- Push to `main` branch triggers automatic deployment
- All tests must pass before deployment
- Docker images are built and published to GitHub Container Registry

### Manual Deployment
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Or using published images
export GITHUB_REPOSITORY=computacenter-ro/case-ai-dynamic-learning-path
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Documentation

- [CI/CD Pipeline Documentation](docs/CI-CD.md)
- [API Documentation](http://localhost:8001/docs) (when running)
- [Frontend Components](fe/components/README.md)
- [Backend Services](be/app/services/README.md)

## 🔧 Development

### Project Structure
```
├── .github/workflows/     # GitHub Actions CI/CD
├── be/                   # FastAPI Backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── tests/           # Backend tests
│   └── Dockerfile
├── fe/                   # Next.js Frontend
│   ├── components/      # React components
│   ├── pages/          # Next.js pages
│   ├── lib/            # Utility libraries
│   ├── types/          # TypeScript types
│   └── Dockerfile
├── docs/                # Documentation
└── scripts/             # Utility scripts
```

### Code Quality
- **Backend**: Flake8 linting, pytest testing
- **Frontend**: ESLint, TypeScript strict mode
- **Security**: Trivy vulnerability scanning
- **Pre-commit**: Automated formatting and linting

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `npm test` and `pytest`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🔒 Security

- **Environment Variables**: Never commit API keys or secrets
- **CORS Configuration**: Properly configured for production
- **Dependency Scanning**: Automated vulnerability checks
- **Container Security**: Regular base image updates

## 📊 Monitoring

- **Health Checks**: Built-in Docker health checks
- **Logging**: Structured logging with configurable levels
- **Error Tracking**: Comprehensive error handling and reporting

## 🔄 CI/CD Pipeline

### Automated Workflows
- **Continuous Integration**: Tests, linting, security scanning
- **Continuous Deployment**: Automated deployments to production
- **Dependency Updates**: Weekly automated dependency updates
- **Container Registry**: Automatic Docker image publishing

### Quality Gates
- All tests must pass
- Code coverage requirements
- Security vulnerability checks
- Successful Docker builds

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/issues)
- **Discussions**: [GitHub Discussions](https://github.com/computacenter-ro/case-ai-dynamic-learning-path/discussions)
- **Documentation**: Check the `docs/` directory

## 📄 License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models and embeddings
- YouTube, Google Books, and Spotify for content APIs
- The open-source community for amazing tools and libraries

---

**Built with ❤️ by the Computacenter Romania Team**
