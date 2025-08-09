"""
Base Django settings for bazary project.

This file contains settings common to all environments.
"""

import os
import sys
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Add apps directory to Python path
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "DJANGO_SECRET_KEY", default="django-insecure-change-me-in-production"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [h.strip() for h in v.split(",")],
)

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_yasg",
    "drf_spectacular",
    # 'django_ratelimit',  # TODO: Enable once Redis is configured
]

LOCAL_APPS = [
    "apps.core",
    "apps.authentication",
    "apps.categories",
    "apps.products",
    "apps.payments",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "apps.core.middleware.RequestSanitizationMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.APISecurityLoggingMiddleware",
    "apps.core.middleware.IPWhitelistMiddleware",
]

ROOT_URLCONF = "bazary.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bazary.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="bazary"),
        "USER": config("DB_USER", default="bazary_user"),
        "PASSWORD": config("DB_PASSWORD", default="bazary_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default=5432, cast=int),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "bazary-cache",
    }
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "authentication.User"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttling.BurstRateThrottle",
        "apps.core.throttling.SustainedRateThrottle",
        "apps.core.throttling.AnonymousThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "burst": "60/min",
        "sustained": "1000/day",
        "anon": "30/hour",
        "login": "5/min",
        "registration": "3/hour",
        "search": "30/min",
        "admin": "100/hour",
        "api_key": "1000/hour",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME", default=15, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME", default=7, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config("JWT_SECRET_KEY", default=SECRET_KEY),
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

# Swagger settings
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    },
    "USE_SESSION_AUTH": False,
    "JSON_EDITOR": True,
    "SUPPORTED_SUBMIT_METHODS": ["get", "post", "put", "delete", "patch"],
}

SWAGGER_USE_COMPAT_RENDERERS = False

REDOC_SETTINGS = {
    "LAZY_RENDERING": False,
}

# Email configuration
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@bazary.com")

# Logging configuration
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
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "bazary": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist and we have permission
try:
    os.makedirs(BASE_DIR / "logs", exist_ok=True)
except PermissionError:
    # In Docker environments, logs directory should be created during build
    # If we can't create it here, it should already exist
    pass

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Rate limiting settings
RATELIMIT_ENABLE = config(
    "RATELIMIT_ENABLE", default=False, cast=bool
)  # Disabled for now
RATELIMIT_USE_CACHE = "default"

# IP Whitelist settings (empty by default)
IP_WHITELIST = config(
    "IP_WHITELIST",
    default="",
    cast=lambda v: [ip.strip() for ip in v.split(",") if ip.strip()],
)
ADMIN_IP_WHITELIST = config(
    "ADMIN_IP_WHITELIST",
    default="",
    cast=lambda v: [ip.strip() for ip in v.split(",") if ip.strip()],
)

# Security headers configuration
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Session security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Additional security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
    )
    SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# API Security settings
API_SECURITY_ENABLED = config("API_SECURITY_ENABLED", default=True, cast=bool)
API_REQUEST_SANITIZATION = config("API_REQUEST_SANITIZATION", default=True, cast=bool)
API_SECURITY_LOGGING = config("API_SECURITY_LOGGING", default=True, cast=bool)

# DRF Spectacular settings for enhanced API documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "🛒 Bazary E-Commerce API",
    "DESCRIPTION": """
# Bazary E-Commerce Backend API

A comprehensive, production-ready e-commerce API built with Django REST Framework.

## 🚀 Key Features
- **Complete E-Commerce Solution**: Products, categories, shopping cart, payments
- **Advanced Search & Filtering**: Multi-field search with faceted filters
- **Payment Integration**: Chapa (Ethiopian) payment gateway with webhook support
- **User Management**: JWT authentication, email verification, admin controls
- **Product Variants**: Size, color, and custom product options
- **Real-time Inventory**: Stock tracking and low-stock alerts
- **Admin Dashboard**: Bulk operations and analytics

## 🔐 Authentication
Most endpoints require JWT authentication. Get your access token from `/api/v1/auth/token/`.

## 📊 API Organization
Endpoints are organized by user journey and logical grouping:
1. **Authentication Flow** - Login, registration, verification
2. **User Management** - Profiles, addresses, activity
3. **Admin Operations** - User & product management
4. **Product Catalog** - Categories, products, variants
5. **Shopping Experience** - Discovery, search, cart
6. **Payment Processing** - Methods, transactions, webhooks
7. **System Utilities** - Health checks, testing guides

## 🧪 Testing
Comprehensive testing guides available for each endpoint group.
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "TAGS": [
        {
            "name": "01 🔐 Authentication",
            "description": "Core authentication endpoints for user login, registration, and session management. Start here for API access.",
        },
        {
            "name": "02 📧 Email Verification",
            "description": "Email verification and account activation endpoints. Required for new user accounts.",
        },
        {
            "name": "03 🔑 Password Management",
            "description": "Password reset and recovery endpoints for account security management.",
        },
        {
            "name": "04 🎫 Token Management",
            "description": "JWT token operations including refresh, verify, and blacklist functionality.",
        },
        {
            "name": "05 👤 User Profile",
            "description": "User profile management, settings, and personal information endpoints.",
        },
        {
            "name": "06 🏠 User Addresses",
            "description": "User shipping and billing address management for checkout and delivery.",
        },
        {
            "name": "07 📊 User Activity",
            "description": "User activity tracking, audit logs, and behavioral analytics.",
        },
        {
            "name": "08 🛡️ Admin - User Management",
            "description": "Administrative user management operations. Requires admin privileges.",
        },
        {
            "name": "09 🛡️ Admin - Product Management",
            "description": "Administrative product management and bulk operations. Requires admin privileges.",
        },
        {
            "name": "11 📂 Categories",
            "description": "Product category management with hierarchical organization support.",
        },
        {
            "name": "12 🏷️ Tags",
            "description": "Product tagging system for flexible organization and filtering.",
        },
        {
            "name": "13 📦 Products",
            "description": "Core product management with CRUD operations, search, and filtering capabilities.",
        },
        {
            "name": "14 🔄 Product Variants",
            "description": "Product variant management for size, color, and other product options.",
        },
        {
            "name": "16 ⚙️ Variant Options",
            "description": "Variant option definitions and value management for product customization.",
        },
        {
            "name": "17 🔍 Product Discovery",
            "description": "Product browsing, featured products, and discovery endpoints for customers.",
        },
        {
            "name": "18 🔎 Search & Filters",
            "description": "Advanced product search with filters, sorting, and faceted search capabilities.",
        },
        {
            "name": "19 🛒 Shopping Cart",
            "description": "Shopping cart operations for managing customer product selections.",
        },
        {
            "name": "21 🏦 Payment Providers",
            "description": "Payment provider configuration and management (Chapa, Stripe, etc.).",
        },
        {
            "name": "22 💳 Payment Methods",
            "description": "Payment method management for customers and transaction processing.",
        },
        {
            "name": "23 💰 Transactions",
            "description": "Transaction processing, tracking, and payment flow management.",
        },
        {
            "name": "24 🔔 Payment Webhooks",
            "description": "Webhook endpoints for payment provider notifications and status updates.",
        },
        {
            "name": "26 🏥 System Health",
            "description": "System health checks, monitoring, and status endpoints.",
        },
        {
            "name": "29 📚 Testing Guides",
            "description": "Comprehensive testing instructions and examples for each API module.",
        },
    ],
    "EXTERNAL_DOCS": {
        "description": "Complete API Documentation & Guides",
        "url": "https://github.com/legennd48/bazary/blob/main/README.md",
    },
    "CONTACT": {
        "name": "Bazary API Support",
        "email": "api-support@bazary.com",
        "url": "https://github.com/legennd48/bazary/issues",
    },
    "LICENSE": {"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    # Postprocessing hooks to tweak schema after generation
    "POSTPROCESSING_HOOKS": [
        "apps.core.schema_hooks.rename_api_tag_to_z_advanced",
    ],
}

# Email Configuration
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@bazary.com")

# Site Configuration
SITE_NAME = config("SITE_NAME", default="Bazary")
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
AVATAR_MAX_SIZE = 2097152  # 2MB

# User Management Settings
USER_EMAIL_VERIFICATION_REQUIRED = config(
    "USER_EMAIL_VERIFICATION_REQUIRED", default=True, cast=bool
)
USER_PASSWORD_RESET_TIMEOUT = config(
    "USER_PASSWORD_RESET_TIMEOUT", default=3600, cast=int  # 1 hour
)
USER_EMAIL_VERIFICATION_TIMEOUT = config(
    "USER_EMAIL_VERIFICATION_TIMEOUT", default=86400, cast=int  # 24 hours
)
