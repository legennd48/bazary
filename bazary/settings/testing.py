"""
Testing settings for bazary project.
"""

from .base import *

# Use in-memory database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations during tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Use dummy cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Disable logging during tests
LOGGING_CONFIG = None

# Use MD5 password hasher for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media files
MEDIA_ROOT = "/tmp/bazary_test_media"

# Secret key for testing
SECRET_KEY = "test-secret-key-only-for-testing"

# Debug
DEBUG = False

# Allowed hosts for testing
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# CORS
CORS_ALLOW_ALL_ORIGINS = True
