"""
CI Testing settings for bazary project.
This configuration is specifically for GitHub Actions CI/CD pipeline.
"""

import os

from .base import *

# Use PostgreSQL database for CI tests (matches production better)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_bazary",
        "USER": "postgres", 
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "test_bazary",
        },
    }
}

# Use Redis for CI tests
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Use MD5 password hasher for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media files
MEDIA_ROOT = "/tmp/bazary_ci_media"

# Static files
STATIC_ROOT = "/tmp/bazary_ci_static"
STATICFILES_DIRS = []

# Swagger settings
SWAGGER_USE_COMPAT_RENDERERS = False

# Secret key for testing
SECRET_KEY = "ci-test-secret-key-only-for-testing"

# Debug settings
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

# Disable logging during tests
import logging

logging.disable(logging.CRITICAL)

# Test specific settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Static files
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Timezone
USE_TZ = True
