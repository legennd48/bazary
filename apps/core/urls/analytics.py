"""
Analytics URL patterns.
"""

from django.urls import path

from apps.core.views.analytics import (
    dashboard_summary,
    sales_summary,
    sales_trend,
    top_products,
    top_categories,
    inventory_report,
    customer_analytics,
    booking_analytics,
)

app_name = "analytics"

urlpatterns = [
    path("dashboard/", dashboard_summary, name="dashboard"),
    path("sales/summary/", sales_summary, name="sales-summary"),
    path("sales/trend/", sales_trend, name="sales-trend"),
    path("products/top/", top_products, name="top-products"),
    path("categories/top/", top_categories, name="top-categories"),
    path("inventory/", inventory_report, name="inventory-report"),
    path("customers/", customer_analytics, name="customer-analytics"),
    path("bookings/", booking_analytics, name="booking-analytics"),
]
