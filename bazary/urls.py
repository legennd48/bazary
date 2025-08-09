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

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="🛒 Bazary E-Commerce API",
        default_version="v1",
        description="""
# Bazary E-Commerce Backend API

Welcome to the comprehensive e-commerce backend API built with Django REST Framework.

## 📋 Overview

This API provides complete e-commerce functionality including:

### 🛍️ Core Features
- **Product Management**: Full CRUD operations with advanced filtering and search
- **Category System**: Hierarchical product organization
- **Tag System**: Flexible product labeling and categorization
- **User Authentication**: JWT-based secure authentication
- **Advanced Search**: Multi-field search with filtering and sorting
- **Stock Management**: Real-time inventory tracking

### 🚀 API Highlights
- **RESTful Design**: Following REST API best practices
- **Comprehensive Documentation**: Detailed endpoint descriptions and examples
- **Testing Instructions**: Built-in testing guides for each module
- **Performance Optimized**: Database query optimization and pagination
- **Security First**: Authentication and permission-based access control

## 🔗 Quick Links
- **Testing Instructions**: Available at `/api/v1/products/testing-instructions/`
- **GitHub Repository**: [Bazary on GitHub](https://github.com/legennd48/bazary)
- **Documentation**: Complete API documentation below

## 🔐 Authentication
Most endpoints require JWT authentication. Get your access token from the `/api/v1/auth/login/` endpoint.

## 📚 API Versioning
All endpoints are versioned with `/api/v1/` prefix for future compatibility.

## 📊 Rate Limiting
API requests are rate-limited to ensure fair usage and optimal performance.

---

**Built with ❤️ using Django REST Framework**
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
                path("tags/", include("apps.products.tag_urls")),  # Tags at root level
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
