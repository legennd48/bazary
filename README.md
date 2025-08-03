# 🛒 Bazary - E-Commerce Backend Platform

[![CI/CD Pipeline](https://github.com/legennd48/bazary/workflows/CI%20Pipeline/badge.svg)](https://github.com/legennd48/bazary/actions)
[![Code Coverage](https://codecov.io/gh/legennd48/bazary/branch/main/graph/badge.svg)](https://codecov.io/gh/legennd48/bazary)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A production-ready Django e-commerce backend with advanced DevOps practices**

Bazary is a robust, scalable Django-based e-commerce backend system designed for real-world production environments. It emphasizes security, performance, and maintainability with comprehensive CI/CD pipelines, containerization, and modern development practices.

## ✨ Key Features

🛍️ **E-Commerce Core**
- Product catalog management with categories and tags
- Advanced filtering, sorting, and search capabilities
- JWT-based authentication and authorization
- Admin panel for product and user management
- RESTful API with comprehensive documentation

🚀 **DevOps Excellence**
- Complete CI/CD pipeline with GitHub Actions
- Docker containerization for development and production
- Git Flow workflow with automated testing
- Multi-environment deployment (dev, staging, production)
- Automated database migrations and static file collection

🔒 **Security & Performance**
- Industry-standard security practices
- Database query optimization with indexing
- Redis caching integration (planned)
- Rate limiting and API throttling
- Comprehensive logging and monitoring

📚 **Developer Experience**
- Extensive documentation and setup guides
- Pre-commit hooks for code quality
- Automated testing with pytest and factory-boy
- Swagger/OpenAPI documentation
- Type hints and comprehensive test coverage

## 🚀 Quick Start

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (for production deployment)

### 1. Clone and Setup

```bash
git clone https://github.com/legennd48/bazary.git
cd bazary
cp .env.example .env.dev
```

### 2. Start Development Environment

```bash
# Start all services
docker-compose up --build

# In a new terminal, run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load sample data (optional)
docker-compose exec web python manage.py loaddata fixtures/sample_data.json
```

### 3. Access the Application

- **🌐 API Base**: http://localhost:8000/api/
- **👤 Admin Panel**: http://localhost:8000/admin/
- **📖 API Docs**: http://localhost:8000/swagger/
- **📚 ReDoc**: http://localhost:8000/redoc/

## 📁 Project Structure

```
bazary/
├── 📁 apps/                    # Django applications
│   ├── authentication/        # User auth & JWT
│   ├── products/              # Product management
│   ├── categories/            # Category system
│   └── core/                  # Shared utilities
├── 📁 bazary/                 # Main Django project
│   └── settings/              # Environment configs
├── 📁 docs/                   # Documentation
├── 📁 docker/                 # Docker configurations
├── 📁 .github/workflows/      # CI/CD pipelines
├── 📁 requirements/           # Dependencies
├── 🐳 docker-compose.yml      # Development setup
├── 🐳 Dockerfile             # Multi-stage build
└── 📋 README.md              # This file
```

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | Django + DRF | 5.0+ |
| **Database** | PostgreSQL | 15+ |
| **Cache** | Redis | 7+ |
| **Authentication** | JWT (SimpleJWT) | Latest |
| **Documentation** | Swagger/OpenAPI | 3.0 |
| **Testing** | Pytest + Factory Boy | Latest |
| **Containerization** | Docker + Compose | Latest |
| **CI/CD** | GitHub Actions | Latest |
| **Code Quality** | Black, Flake8, isort | Latest |

## 📖 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[🏗️ Technical Architecture](./docs/technical-architecture.md)** - System design and components
- **[🚀 DevOps Guide](./docs/devops-guide.md)** - CI/CD, Docker, and Git workflows
- **[🌐 Deployment Guide](./docs/deployment-guide.md)** - Production deployment instructions
- **[💻 Development Guide](./docs/development-guide.md)** - Local setup and coding standards
- **[📊 Database Schema](./docs/database-schema.md)** - Data models and relationships
- **[🔐 Security Guide](./docs/security-guide.md)** - Security practices (coming soon)
- **[🧪 Testing Strategy](./docs/testing-strategy.md)** - Testing approach (coming soon)

## 🏃‍♂️ Development Workflow

### Git Flow Process

```bash
# Start new feature
git flow feature start user-authentication

# Work on feature...
git add .
git commit -m "feat(auth): implement JWT authentication"

# Finish feature
git flow feature finish user-authentication
```

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run quality checks
black .           # Format code
flake8 .          # Lint code
isort .           # Sort imports
pytest            # Run tests
pytest --cov     # Check coverage
```

### Docker Development

```bash
# Start development environment
docker-compose up --build

# Run commands in container
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py test

# View logs
docker-compose logs -f web
```

## 🚀 Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy to staging
railway up --service staging

# Deploy to production
railway up --service production
```

### Other Platforms

The application supports deployment to:
- **Railway** (Recommended)
- **Render**
- **DigitalOcean App Platform**
- **Custom VPS with Docker**

See the [Deployment Guide](./docs/deployment-guide.md) for detailed instructions.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest apps/products/tests/test_models.py

# Run tests in parallel
pytest -n auto
```

## 📊 API Examples

### Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

### Products

```bash
# List products
curl http://localhost:8000/api/products/

# Filter products
curl "http://localhost:8000/api/products/?category=electronics&price_min=50"

# Create product (admin only)
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Product", "price": "99.99", "category": 1}'
```

## 🗺️ Roadmap

### ✅ Phase 1: Core MVP (Current)
- [x] Project setup and documentation
- [x] Docker development environment
- [x] CI/CD pipeline configuration
- [ ] User authentication system
- [ ] Product management APIs
- [ ] Category system
- [ ] API documentation

### 🚧 Phase 2: Enhanced Features
- [ ] Shopping cart functionality
- [ ] Order management system
- [ ] Payment integration (Stripe)
- [ ] Email notifications
- [ ] Advanced search with Elasticsearch
- [ ] Image upload and optimization

### 🔮 Phase 3: Hybrid Commerce
- [ ] Service booking system
- [ ] Appointment scheduling
- [ ] Multi-vendor marketplace
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Follow** our coding standards and write tests
4. **Commit** using conventional commit messages
5. **Push** to your branch and create a Pull Request

### Commit Convention

```bash
feat(scope): add new feature
fix(scope): bug fix
docs(scope): documentation update
style(scope): formatting changes
refactor(scope): code refactoring
test(scope): add tests
chore(scope): maintenance tasks
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Django** and **Django REST Framework** communities
- **Railway** for excellent hosting platform
- **GitHub Actions** for CI/CD infrastructure
- All the amazing open-source contributors

## 📞 Support & Contact

- **📋 Issues**: [GitHub Issues](https://github.com/legennd48/bazary/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/legennd48/bazary/discussions)
- **📧 Email**: [Contact](mailto:your-email@domain.com)
- **📖 Wiki**: [Project Wiki](https://github.com/legennd48/bazary/wiki)

---

**⭐ Star this repository if you find it helpful!**

Built with ❤️ by [legennd48](https://github.com/legennd48) and contributors.
