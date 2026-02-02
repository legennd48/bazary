"""
Capability-aware URL routing.

This module provides functions to build URL patterns based on
which capabilities are enabled for the current deployment.
"""

from typing import List, Tuple

from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path


def get_capability_urls() -> List[Tuple[str, str, str]]:
    """
    Get URL patterns for enabled capabilities.
    
    Returns:
        List of (path_prefix, module_path, namespace) tuples.
    """
    enabled = set(getattr(settings, "ENABLED_CAPABILITIES", []))
    urls = []
    
    # Core auth is always available
    urls.append(("auth/", "apps.authentication.urls", "authentication"))
    
    # Vendors (multi-vendor marketplace) - always available
    urls.append(("vendors/", "apps.authentication.urls_vendor", "vendors"))
    
    # Analytics (admin only) - always available
    urls.append(("analytics/", "apps.core.urls.analytics", "analytics"))
    
    # Products capability
    if "products" in enabled:
        urls.append(("categories/", "apps.categories.urls", "categories"))
        urls.append(("products/", "apps.products.urls", "products"))
        urls.append(("wishlists/", "apps.products.urls_wishlist", "wishlists"))
    
    # Services capability
    if "services" in enabled:
        urls.append(("services/", "apps.services.urls", "services"))
    
    # Bookings capability
    if "bookings" in enabled:
        urls.append(("bookings/", "apps.bookings.urls", "bookings"))
    
    # Orders capability
    if "orders" in enabled:
        urls.append(("orders/", "apps.orders.urls", "orders"))
    
    # Payments capability (depends on orders)
    if "payments" in enabled:
        urls.append(("payments/", "apps.payments.urls", "payments"))
    
    # Notifications capability
    if "notifications" in enabled:
        urls.append(("notifications/", "apps.notifications.urls", "notifications"))
    
    return urls


def build_api_v1_patterns() -> List[URLPattern | URLResolver]:
    """
    Build API v1 URL patterns based on enabled capabilities.
    """
    patterns = []
    
    for path_prefix, module_path, namespace in get_capability_urls():
        try:
            patterns.append(
                # When specifying a namespace, Django requires an app_name.
                # Provide it via the 2-tuple form to avoid requiring every
                # included urls.py to define `app_name`.
                path(path_prefix, include((module_path, namespace), namespace=namespace))
            )
        except ImportError:
            # Module doesn't exist yet - skip
            pass
    
    return patterns


def build_api_v2_patterns() -> List[URLPattern | URLResolver]:
    """
    Build API v2 URL patterns based on enabled capabilities.
    
    V2 uses the same capability gating but may have different
    endpoints/serializers.
    """
    enabled = set(getattr(settings, "ENABLED_CAPABILITIES", []))
    patterns = []
    
    # Platform info endpoint (always available)
    patterns.append(
        path(
            "platform/",
            include(("apps.core.urls_v2", "platform"), namespace="platform"),
        )
    )
    
    # Add v2 endpoints for enabled capabilities
    # These will be added as v2 modules are created
    
    return patterns
