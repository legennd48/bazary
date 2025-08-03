"""
Django settings for testing environment - optimized for CI/CD pipeline.
"""

from .base import *

# Override for testing
DEBUG = False
TESTING = True

# Database configuration for testing
if os.environ.get("DATABASE_URL"):
    # PostgreSQL for CI/CD
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(os.environ.get("DATABASE_URL"))}
else:
    # SQLite for local testing
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Cache configuration for testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Static files for testing
STATIC_ROOT = os.path.join(BASE_DIR, "test_staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "test_media")

# Security settings for testing
SECRET_KEY = "test-secret-key-for-ci-cd-pipeline-do-not-use-in-production"

# Logging configuration for testing
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Only disable migrations in unit tests, not in CI/CD
if "test" in sys.argv:
    MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",  # Faster for testing
]

# API settings for testing
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

# Allow all hosts in testing
ALLOWED_HOSTS = ["*"]

# CORS settings for testing
CORS_ALLOW_ALL_ORIGINS = True
