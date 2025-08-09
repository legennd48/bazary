"""
URL configuration for bazary project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="🛒 Bazary E-Commerce API",
        default_version="v1",
    description="""
Welcome to the comprehensive e-commerce backend API built with Django REST Framework.

Overview

This API powers a full e-commerce backend: products, categories, tags, carts, payments, and user accounts.

Auth
- Most endpoints require JWT. Obtain tokens via `/api/v1/auth/login/`.

Versioning
- All endpoints are prefixed with `/api/v1/`.

Quick links
- Testing instructions: `/api/v1/products/testing-instructions/`
- GitHub: https://github.com/legennd48/bazary

Notes
- Pagination, filtering, and permissions follow DRF best practices.
- See each endpoint for examples and request/response schemas.
        """,
        terms_of_service="https://bazary.com/terms/",
        contact=openapi.Contact(
            name="Bazary API Support",
            email="api-support@bazary.com",
            url="https://bazary.com/support/",
        ),
        license=openapi.License(
            name="MIT License", url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API URLs v1
    path(
        "api/v1/",
        include(
            [
                path("auth/", include("apps.authentication.urls")),
                path("categories/", include("apps.categories.urls")),
                path("products/", include("apps.products.urls")),
                # Tags are available at /api/v1/products/tags/ - no need for separate /tags/ endpoint
                path("payments/", include("apps.payments.urls")),  # Payment & Cart APIs
            ]
        ),
    ),
    # API Documentation
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Spectacular schema and UI (recommended for extend_schema annotations)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="spectacular-swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="spectacular-redoc",
    ),
    # Health check
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
