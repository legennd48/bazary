# Multi-stage Docker build for production optimization
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Development stage
FROM base as development

# Copy requirements first
COPY requirements/ /app/requirements/
# Install development dependencies
RUN pip install -r requirements/development.txt

# Copy project
COPY . /app/

# Create necessary directories and files with proper permissions
RUN mkdir -p /app/logs && \
    mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    mkdir -p /app/static && \
    touch /app/logs/django.log

# Change ownership of the app directory
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base as production

# Copy requirements first
COPY requirements/ /app/requirements/
# Install production dependencies
RUN pip install -r requirements/production.txt

# Copy project
COPY . /app/

# Create necessary directories and files with proper permissions
RUN mkdir -p /app/logs && \
    mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    mkdir -p /app/static && \
    touch /app/logs/django.log

# Change ownership first, then switch user
RUN chown -R appuser:appuser /app
USER appuser

# Collect static files (will be done at runtime with proper env vars)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health/ || exit 1

# Command for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "bazary.wsgi:application"]
