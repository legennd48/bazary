"""
Analytics API Views.

Admin endpoints for business analytics and reporting.
"""

from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from django.utils import timezone

from apps.core.analytics import AnalyticsService


@api_view(["GET"])
@permission_classes([IsAdminUser])
def dashboard_summary(request):
    """
    Get dashboard summary with key metrics.
    
    Returns comprehensive overview of business performance.
    """
    try:
        summary = AnalyticsService.get_dashboard_summary()
        return Response(summary)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def sales_summary(request):
    """
    Get sales summary for a period.
    
    Query params:
    - start_date: ISO date string (default: 30 days ago)
    - end_date: ISO date string (default: now)
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    
    summary = AnalyticsService.get_sales_summary(start_date, end_date)
    return Response(summary.to_dict())


@api_view(["GET"])
@permission_classes([IsAdminUser])
def sales_trend(request):
    """
    Get sales trend over time.
    
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    - granularity: 'day', 'week', or 'month' (default: 'day')
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    granularity = request.query_params.get("granularity", "day")
    
    if granularity not in ["day", "week", "month"]:
        granularity = "day"
    
    trend = AnalyticsService.get_sales_trend(start_date, end_date, granularity)
    return Response({
        "granularity": granularity,
        "data": trend,
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def top_products(request):
    """
    Get top-selling products.
    
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    - limit: Number of products (default: 10)
    - by: 'revenue' or 'units' (default: 'revenue')
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    limit = int(request.query_params.get("limit", 10))
    by = request.query_params.get("by", "revenue")
    
    if by not in ["revenue", "units"]:
        by = "revenue"
    
    products = AnalyticsService.get_top_products(start_date, end_date, limit, by)
    return Response({
        "sorted_by": by,
        "products": [p.to_dict() for p in products],
    })


@api_view(["GET"])
@permission_classes([IsAdminUser])
def top_categories(request):
    """
    Get top-selling categories.
    
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    - limit: Number of categories (default: 10)
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    limit = int(request.query_params.get("limit", 10))
    
    categories = AnalyticsService.get_top_categories(start_date, end_date, limit)
    return Response({"categories": categories})


@api_view(["GET"])
@permission_classes([IsAdminUser])
def inventory_report(request):
    """
    Get inventory status report.
    
    Returns current inventory levels and alerts.
    """
    report = AnalyticsService.get_inventory_report()
    return Response(report)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def customer_analytics(request):
    """
    Get customer analytics.
    
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    
    analytics = AnalyticsService.get_customer_analytics(start_date, end_date)
    return Response(analytics)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def booking_analytics(request):
    """
    Get booking/service analytics.
    
    Query params:
    - start_date: ISO date string
    - end_date: ISO date string
    """
    start_date = _parse_date(request.query_params.get("start_date"))
    end_date = _parse_date(request.query_params.get("end_date"))
    
    analytics = AnalyticsService.get_booking_analytics(start_date, end_date)
    return Response(analytics)


def _parse_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime."""
    if not date_str:
        return None
    try:
        # Try full ISO format
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            # Try date-only format
            from django.utils.dateparse import parse_date
            parsed = parse_date(date_str)
            if parsed:
                return timezone.make_aware(datetime.combine(parsed, datetime.min.time()))
        except Exception:
            pass
    return None
