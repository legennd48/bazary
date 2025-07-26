# 🚀 Deployment Guide

## 🎯 Deployment Strategy Overview

Bazary supports multiple deployment platforms with containerized deployment for consistency and scalability.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Development │───▶│   Staging   │───▶│ Production  │
│             │    │             │    │             │
│ Local       │    │ Railway     │    │ Railway/DO  │
│ Docker      │    │ Auto-deploy │    │ Manual      │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🛠️ Platform Options

### 1. Railway (Recommended)
- **Pros**: Django-friendly, automatic deployments, built-in PostgreSQL
- **Cons**: Limited free tier
- **Best for**: MVP and production deployments

### 2. Render
- **Pros**: Free tier available, easy setup
- **Cons**: Cold starts on free tier
- **Best for**: Development and staging

### 3. DigitalOcean App Platform
- **Pros**: Scalable, good performance
- **Cons**: More expensive for small apps
- **Best for**: Production scaling

### 4. AWS/GCP (Future)
- **Pros**: Full control, enterprise-grade
- **Cons**: Complex setup, higher costs
- **Best for**: Large-scale production

## 🚂 Railway Deployment

### Initial Setup

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

2. **Create Railway Project**
```bash
railway init
railway add --service postgresql
railway add --service redis
```

3. **Configure Environment Variables**
```bash
railway variables set DJANGO_SECRET_KEY=your-secret-key
railway variables set DJANGO_DEBUG=False
railway variables set DJANGO_ALLOWED_HOSTS=your-domain.railway.app
railway variables set DATABASE_URL=${{Postgres.DATABASE_URL}}
railway variables set REDIS_URL=${{Redis.REDIS_URL}}
```

### Railway Configuration Files

```toml
# railway.toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements/production.txt && python manage.py collectstatic --noinput"

[deploy]
startCommand = "python manage.py migrate && gunicorn bazary.wsgi:application --bind 0.0.0.0:$PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[env]
DJANGO_SETTINGS_MODULE = "bazary.settings.production"
PORT = "8000"
```

```dockerfile
# Dockerfile.railway
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && gunicorn bazary.wsgi:application --bind 0.0.0.0:$PORT"]
```

### Environment-Specific Settings

```python
# settings/production.py
import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    'bazary-production.railway.app',
    'yourdomain.com',
    'www.yourdomain.com'
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE'),
        'USER': os.environ.get('PGUSER'),
        'PASSWORD': os.environ.get('PGPASSWORD'),
        'HOST': os.environ.get('PGHOST'),
        'PORT': os.environ.get('PGPORT', 5432),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Use HTTPS
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## 🌟 Render Deployment

### render.yaml

```yaml
# render.yaml
services:
  - type: web
    name: bazary-web
    env: python
    region: oregon
    plan: starter
    buildCommand: "pip install -r requirements/production.txt && python manage.py collectstatic --noinput"
    startCommand: "python manage.py migrate && gunicorn bazary.wsgi:application"
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: bazary.settings.production
      - key: DJANGO_SECRET_KEY
        generateValue: true
      - key: DJANGO_DEBUG
        value: False
      - key: DATABASE_URL
        fromDatabase:
          name: bazary-db
          property: connectionString
    domains:
      - bazary.onrender.com

databases:
  - name: bazary-db
    databaseName: bazary
    user: bazary_user
    region: oregon
    plan: starter
```

## 🐙 DigitalOcean App Platform

### .do/app.yaml

```yaml
# .do/app.yaml
name: bazary
services:
  - name: web
    source_dir: /
    github:
      repo: legennd48/bazary
      branch: main
      deploy_on_push: true
    run_command: gunicorn --worker-tmp-dir /dev/shm bazary.wsgi:application
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8080
    routes:
      - path: /
    health_check:
      http_path: /health/
    envs:
      - key: DJANGO_SETTINGS_MODULE
        value: bazary.settings.production
      - key: DJANGO_SECRET_KEY
        value: ${bazary.DJANGO_SECRET_KEY}
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}

databases:
  - name: db
    engine: PG
    size: basic-xs
    num_nodes: 1
    version: "15"

workers:
  - name: worker
    source_dir: /
    github:
      repo: legennd48/bazary
      branch: main
    run_command: python manage.py rqworker
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: DJANGO_SETTINGS_MODULE
        value: bazary.settings.production
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
```

## 🔧 Custom VPS Deployment

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_volume:/static
      - media_volume:/media
    depends_on:
      - web
    restart: unless-stopped

  web:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    environment:
      - DJANGO_SETTINGS_MODULE=bazary.settings.production
      - DATABASE_URL=postgresql://bazary_user:${POSTGRES_PASSWORD}@db:5432/bazary
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=bazary
      - POSTGRES_USER=bazary_user
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - ./nginx/ssl:/etc/letsencrypt
      - ./nginx/ssl-dhparams.pem:/etc/letsencrypt/ssl-dhparams.pem
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

### Nginx Configuration

```nginx
# nginx/nginx.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://django;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
    
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Starting deployment..."

# Pull latest changes
git pull origin main

# Build and deploy
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Health check
sleep 30
if curl -f http://localhost/health/; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed - rolling back"
    docker-compose -f docker-compose.prod.yml down
    exit 1
fi

echo "🎉 Deployment completed successfully!"
```

## 📊 Monitoring & Maintenance

### Database Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bazary_backup_$DATE.sql"

# Create backup
docker-compose exec -T db pg_dump -U bazary_user bazary > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_FILE.gz"
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

HEALTH_URL="https://yourdomain.com/health/"
WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL"

if curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 Bazary health check failed!"}' \
        $WEBHOOK_URL
    exit 1
fi
```

### Monitoring Crontab

```bash
# Add to crontab (crontab -e)

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh

# Health check every 5 minutes
*/5 * * * * /path/to/health_check.sh

# Certificate renewal check
0 0,12 * * * /path/to/ssl_renewal.sh
```

## 🔐 Security Checklist

### Pre-Deployment Security

- [ ] Environment variables properly configured
- [ ] Debug mode disabled in production
- [ ] Secret key using secure random value
- [ ] Database credentials secured
- [ ] HTTPS enabled and enforced
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection protection verified
- [ ] XSS protection enabled

### Post-Deployment Security

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall rules configured
- [ ] Database access restricted
- [ ] Backup and recovery procedures tested
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup
- [ ] Intrusion detection configured
- [ ] Regular security updates scheduled

## 📈 Performance Optimization

### Database Optimization

```python
# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

### Static File Optimization

```python
# Static files configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Compression
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ... other middleware
]
```

This deployment guide provides comprehensive instructions for deploying Bazary to various platforms with proper security, monitoring, and maintenance procedures.
