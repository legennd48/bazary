# 🚀 DevOps Guide - CI/CD, Docker & Deployment

## 🎯 DevOps Strategy Overview

Our DevOps approach emphasizes automation, reliability, and scalability with industry best practices.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Development │───▶│   Staging   │───▶│ Production  │───▶│ Monitoring  │
│             │    │             │    │             │    │             │
│ • Feature   │    │ • Testing   │    │ • Live App  │    │ • Metrics   │
│ • Testing   │    │ • QA        │    │ • Users     │    │ • Alerts    │
│ • Review    │    │ • Demo      │    │ • Analytics │    │ • Logs      │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 🌿 Git Workflow Strategy

### Git Flow Implementation

We use **Git Flow** with the following branch structure:

```
main                    # Production-ready code
├── develop            # Integration branch
├── feature/*          # New features
├── release/*          # Release preparation
├── hotfix/*           # Emergency fixes
└── support/*          # Maintenance
```

### Branch Protection Rules

**Main Branch:**
- Require pull request reviews (2 reviewers)
- Require status checks to pass
- Require branches to be up to date
- Restrict pushes to admins only
- Require conversation resolution

**Develop Branch:**
- Require pull request reviews (1 reviewer)
- Require status checks to pass
- Allow admins to bypass requirements

### Commit Message Convention

```bash
# Format: <type>[optional scope]: <description>
# Types: feat, fix, docs, style, refactor, perf, test, chore

feat(auth): add JWT token refresh endpoint
fix(products): resolve pagination issue with large datasets
docs(api): update swagger documentation for filtering
perf(db): add indexes for product search optimization
test(auth): add comprehensive JWT validation tests
chore(deps): update Django to 5.0.1
```

### Workflow Commands

```bash
# Start new feature
git flow feature start user-authentication
git flow feature finish user-authentication

# Create release
git flow release start v1.0.0
git flow release finish v1.0.0

# Emergency hotfix
git flow hotfix start critical-security-fix
git flow hotfix finish critical-security-fix
```

## 🐳 Docker Configuration

### Multi-Stage Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Development stage
FROM base as development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/development.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy application code
COPY . /app/

# Development command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/production.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER appuser

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "bazary.wsgi:application"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - static_volume:/app/static
      - media_volume:/app/media
    environment:
      - DEBUG=1
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python manage.py runserver 0.0.0.0:8000

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/static
      - media_volume:/media
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/static
      - media_volume:/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

## ⚙️ CI/CD Pipeline with GitHub Actions

### Workflow Structure

```
.github/
└── workflows/
    ├── ci.yml                 # Continuous Integration
    ├── cd-staging.yml         # Deploy to Staging
    ├── cd-production.yml      # Deploy to Production
    ├── security-scan.yml      # Security checks
    └── dependency-update.yml  # Automated dependency updates
```

### Continuous Integration Pipeline

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ develop, main ]
  pull_request:
    branches: [ develop, main ]

env:
  PYTHON_VERSION: '3.11'
  POSTGRES_VERSION: '15'

jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort bandit safety
          
      - name: Run Black (formatting check)
        run: black --check .
        
      - name: Run Flake8 (linting)
        run: flake8 .
        
      - name: Run isort (import sorting)
        run: isort --check-only .
        
      - name: Run Bandit (security check)
        run: bandit -r . -x tests/
        
      - name: Run Safety (dependency vulnerability check)
        run: safety check

  test:
    runs-on: ubuntu-latest
    needs: lint-and-format
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_bazary
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements/testing.txt') }}
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements/testing.txt
          
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_bazary
          DJANGO_SETTINGS_MODULE: bazary.settings.testing
        run: python manage.py migrate
        
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_bazary
          DJANGO_SETTINGS_MODULE: bazary.settings.testing
        run: |
          pytest --cov=. --cov-report=xml --cov-report=html
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests

  build-docker:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Staging Deployment Pipeline

```yaml
# .github/workflows/cd-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [ develop ]

jobs:
  deploy-staging:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Railway (Staging)
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          npm install -g @railway/cli
          railway login --token $RAILWAY_TOKEN
          railway up --service staging
          
      - name: Run database migrations
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          railway run --service staging python manage.py migrate
          
      - name: Collect static files
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          railway run --service staging python manage.py collectstatic --noinput
          
      - name: Health check
        run: |
          sleep 30
          curl -f https://bazary-staging.railway.app/health/ || exit 1
          
      - name: Notify deployment success
        uses: 8398a7/action-slack@v3
        with:
          status: success
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Production Deployment Pipeline

```yaml
# .github/workflows/cd-production.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'
  release:
    types: [published]

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Approval gate
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: legennd48
          minimum-approvals: 1
          
      - name: Deploy to Railway (Production)
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_PROD }}
        run: |
          npm install -g @railway/cli
          railway login --token $RAILWAY_TOKEN
          railway up --service production
          
      - name: Database backup before migration
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          # Create backup before migration
          pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
          
      - name: Run database migrations
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN_PROD }}
        run: |
          railway run --service production python manage.py migrate
          
      - name: Health check
        run: |
          sleep 60
          curl -f https://bazary.railway.app/health/ || exit 1
          
      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          channel: '#deployments'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🔐 Environment Management

### GitHub Environments

**Development Environment:**
- Automatic deployment on feature branch pushes
- No approval required
- Limited secrets access

**Staging Environment:**
- Deployment on `develop` branch
- QA team access
- Production-like configuration

**Production Environment:**
- Manual approval required
- Admin-only access
- Full monitoring and alerting

### Secrets Management

```yaml
# GitHub Secrets Structure
Repository Secrets:
  - DOCKER_USERNAME
  - DOCKER_PASSWORD
  - CODECOV_TOKEN
  - SLACK_WEBHOOK

Environment Secrets:
  staging:
    - RAILWAY_TOKEN
    - DATABASE_URL
    - DJANGO_SECRET_KEY
    - SENTRY_DSN
    
  production:
    - RAILWAY_TOKEN_PROD
    - DATABASE_URL_PROD
    - DJANGO_SECRET_KEY_PROD
    - SENTRY_DSN_PROD
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
```

## 📊 Monitoring & Observability

### Health Check Endpoint

```python
# apps/core/views.py
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
import redis

def health_check(request):
    """System health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        db_conn = connections['default']
        db_conn.cursor()
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Redis check
    try:
        cache.get('health_check')
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
```

### Logging Configuration

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

## 📈 Performance Monitoring

### Sentry Integration

```python
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
            signals_spans=True,
        ),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment=env('ENVIRONMENT', default='production'),
)
```

This comprehensive DevOps setup ensures reliable, automated, and scalable deployment processes with proper monitoring and observability.
