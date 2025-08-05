"""
Development settings for bazary project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Database for development - use PostgreSQL in Docker or SQLite locally
import os
from decouple import config

if config('DATABASE_URL', default=None):
    # Use PostgreSQL when DATABASE_URL is provided (Docker environment)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(config('DATABASE_URL'))
    }
else:
    # Use SQLite for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Development cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bazary-dev-cache",
    }
}

# Add development-specific apps
INSTALLED_APPS += [
    "django_extensions",
]

# Add debug toolbar if available
try:
    import debug_toolbar

    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

    # Debug Toolbar configuration
    INTERNAL_IPS = [
        "127.0.0.1",
        "localhost",
    ]

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    }
except ImportError:
    pass

# Security settings for development - disable HTTPS redirect
SECURE_SSL_REDIRECT = False

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable caching in development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Static files configuration for development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Logging for development - use console logging instead of file logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "bazary": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
