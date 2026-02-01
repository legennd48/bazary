"""
Capability-aware settings configuration.

This module provides functions to dynamically configure Django settings
based on enabled platform capabilities.
"""

from typing import List, Tuple

from decouple import config


def get_enabled_capabilities() -> List[str]:
    """
    Get the list of enabled capabilities from environment.
    
    Set via ENABLED_CAPABILITIES env var, comma-separated.
    Example: ENABLED_CAPABILITIES=products,orders,payments
    
    Returns:
        List of capability names to enable.
    """
    # Core is always enabled implicitly
    capabilities_str = config(
        "ENABLED_CAPABILITIES",
        default="products,orders,payments",  # Default: basic e-commerce
    )
    
    capabilities = [
        cap.strip().lower()
        for cap in capabilities_str.split(",")
        if cap.strip()
    ]
    
    return capabilities


def get_capability_apps(enabled_capabilities: List[str]) -> List[str]:
    """
    Get Django apps to install based on enabled capabilities.
    
    Maps capability names to their Django apps.
    Core apps are always included.
    """
    # Core apps (always installed)
    apps = [
        "apps.core",
        "apps.authentication",
    ]
    
    # Capability to apps mapping
    capability_apps = {
        "products": [
            "apps.categories",
            "apps.products",
        ],
        "services": [
            "apps.services",
        ],
        "bookings": [
            "apps.bookings",
        ],
        "orders": [
            "apps.orders",
        ],
        "payments": [
            "apps.payments",
        ],
        "notifications": [
            "apps.notifications",
        ],
    }
    
    # Add apps for enabled capabilities
    seen = set(apps)
    for cap_name in enabled_capabilities:
        cap_apps = capability_apps.get(cap_name, [])
        for app in cap_apps:
            if app not in seen:
                apps.append(app)
                seen.add(app)
    
    return apps


def get_third_party_apps(enabled_capabilities: List[str]) -> List[str]:
    """
    Get third-party apps based on enabled capabilities.
    """
    apps = [
        "rest_framework",
        "rest_framework_simplejwt",
        "rest_framework_simplejwt.token_blacklist",
        "corsheaders",
        "django_filters",
        "drf_spectacular",
    ]
    
    # Add channels if notifications enabled
    if "notifications" in enabled_capabilities:
        apps.insert(0, "channels")
    
    return apps


def get_middleware(enabled_capabilities: List[str]) -> List[str]:
    """
    Get middleware stack based on enabled capabilities.
    """
    middleware = [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        # Custom security middleware
        "apps.core.middleware.SecurityHeadersMiddleware",
        "apps.core.middleware.RequestSanitizationMiddleware",
        "apps.core.middleware.APISecurityLoggingMiddleware",
    ]
    
    return middleware


def configure_capabilities() -> Tuple[List[str], List[str], List[str]]:
    """
    Main configuration function.
    
    Configures the capability registry and returns app/middleware lists.
    
    Returns:
        Tuple of (third_party_apps, local_apps, middleware)
    """
    enabled = get_enabled_capabilities()
    
    # Configure the capability registry singleton
    from apps.core.capabilities.registry import capabilities
    capabilities.configure(enabled)
    
    third_party_apps = get_third_party_apps(enabled)
    local_apps = get_capability_apps(enabled)
    middleware = get_middleware(enabled)
    
    return third_party_apps, local_apps, middleware
