"""
URL configuration for bazary project.

Capability-aware routing: only enabled capabilities register their URLs.
Disabled capabilities have no routes, no attack surface.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .urls_capability import build_api_v1_patterns, build_api_v2_patterns

# Build capability-aware API patterns
api_v1_patterns = build_api_v1_patterns()
api_v2_patterns = build_api_v2_patterns()

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # API v1 (capability-gated)
    path("api/v1/", include((api_v1_patterns, "api_v1"))),
    
    # API v2 (capability-gated, new resource modeling)
    path("api/v2/", include((api_v2_patterns, "api_v2"))),
    
    # API Documentation (drf-spectacular)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    
    # Health check and platform info
    path("health/", include("apps.core.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add debug toolbar URLs if available
    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
