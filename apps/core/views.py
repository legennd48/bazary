"""
Core views for health checks and utilities.
"""

from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apps.core.swagger_docs import SwaggerTags


@swagger_auto_schema(
    method="get",
    tags=[SwaggerTags.SYSTEM_HEALTH],
    operation_summary="System Health Check",
    operation_description="""
    Comprehensive system health check endpoint that verifies the status of critical services.
    
    ### Health Status Levels:
    - **healthy**: All services are operational
    - **degraded**: Minor issues (e.g., cache unavailable)
    - **unhealthy**: Critical issues (e.g., database unavailable)
    
    ### Services Monitored:
    - **Database**: PostgreSQL connection and query execution
    - **Cache**: Redis/cache backend availability
    
    ### Response Format:
    - `status`: Overall system health (healthy/degraded/unhealthy)
    - `timestamp`: ISO 8601 timestamp of health check
    - `services`: Individual service status details
    
    ### Use Cases:
    - Load balancer health checks
    - Monitoring system integration
    - DevOps status verification
    - Automated deployment validation
    """,
    responses={
        200: openapi.Response(
            "System is healthy",
            examples={
                "application/json": {
                    "status": "healthy",
                    "timestamp": "2025-01-28T12:00:00.000Z",
                    "services": {"database": "healthy", "cache": "healthy"},
                }
            },
        ),
        503: openapi.Response(
            "System is unhealthy or degraded",
            examples={
                "application/json": {
                    "status": "unhealthy",
                    "timestamp": "2025-01-28T12:00:00.000Z",
                    "services": {
                        "database": "unhealthy: connection refused",
                        "cache": "degraded: timeout",
                    },
                }
            },
        ),
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify system status.
    """
    health_status = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "services": {},
    }

    # Database check
    try:
        db_conn = connections["default"]
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Cache check (if Redis is configured)
    try:
        cache.get("health_check")
        health_status["services"]["cache"] = "healthy"
    except Exception as e:
        health_status["services"]["cache"] = f"degraded: {str(e)}"
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)


# =============================================================================
# PLATFORM CAPABILITY VIEWS (API v2)
# =============================================================================

from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiExample


class PlatformCapabilitiesView(APIView):
    """
    Returns the list of enabled capabilities for this deployment.
    
    This endpoint allows frontends to dynamically adapt their UI
    based on which backend capabilities are available.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get Platform Capabilities",
        description="""
        Returns information about which platform capabilities are enabled
        for this deployment.
        
        Use this endpoint to:
        - Determine which features to show in the frontend
        - Conditionally load modules/components
        - Display appropriate navigation items
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "enabled": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of enabled capability names",
                    },
                    "available": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "display_name": {"type": "string"},
                                "description": {"type": "string"},
                                "enabled": {"type": "boolean"},
                            },
                        },
                    },
                },
            },
        },
        examples=[
            OpenApiExample(
                "E-commerce deployment",
                value={
                    "enabled": ["core", "products", "orders", "payments"],
                    "available": [
                        {
                            "name": "products",
                            "display_name": "Products & Catalog",
                            "description": "Physical and digital product catalog",
                            "enabled": True,
                        },
                        {
                            "name": "services",
                            "display_name": "Service Offerings",
                            "description": "Service catalog with providers",
                            "enabled": False,
                        },
                    ],
                },
            ),
        ],
        tags=["Platform"],
    )
    def get(self, request):
        from apps.core.capabilities import capabilities
        return Response(capabilities.get_capability_info())


class PlatformConfigView(APIView):
    """
    Returns the client configuration for this deployment.
    
    Includes branding, currency, locale, and other per-client settings
    that the frontend needs to render correctly.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get Platform Configuration",
        description="""
        Returns the client-specific configuration for this deployment.
        
        Use this endpoint to get:
        - Branding information (name, logo, colors)
        - Currency and locale settings
        - Feature flags and business rules
        - Support contact information
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string"},
                    "client_name": {"type": "string"},
                    "currency": {"type": "object"},
                    "branding": {"type": "object"},
                    "locale": {"type": "object"},
                    "features": {"type": "object"},
                },
            },
        },
        tags=["Platform"],
    )
    def get(self, request):
        from apps.core.capabilities.client_config import get_client_config
        config = get_client_config()
        return Response(config.to_dict())


class PlatformHealthView(APIView):
    """
    Detailed platform health check for API v2.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Platform Health Check",
        description="Returns detailed health status of platform services.",
        responses={200: {"type": "object"}},
        tags=["Platform"],
    )
    def get(self, request):
        from django.core.cache import cache
        from django.db import connections
        from django.utils import timezone
        
        health_status = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "version": "2.0.0",
            "services": {},
        }

        # Database check
        try:
            db_conn = connections["default"]
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["services"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["status"] = "unhealthy"

        # Cache check
        try:
            cache.set("health_check", "ok", timeout=10)
            cache.get("health_check")
            health_status["services"]["cache"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["cache"] = {
                "status": "degraded",
                "error": str(e),
            }
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"

        # Capabilities info
        from apps.core.capabilities import capabilities
        health_status["capabilities"] = list(capabilities.get_enabled())

        return Response(health_status)
