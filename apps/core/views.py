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
    tags=[SwaggerTags.HEALTH],
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
