"""
Analytics Service and API.

Provides sales analytics, inventory reports, and business insights.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import logging

from django.db import models
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class SalesSummary:
    """Sales summary data."""
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal
    total_items_sold: int
    unique_customers: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_revenue": str(self.total_revenue),
            "total_orders": self.total_orders,
            "average_order_value": str(self.average_order_value),
            "total_items_sold": self.total_items_sold,
            "unique_customers": self.unique_customers,
        }


@dataclass
class TopProduct:
    """Top-selling product data."""
    product_id: str
    product_name: str
    units_sold: int
    revenue: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "units_sold": self.units_sold,
            "revenue": str(self.revenue),
        }


class AnalyticsService:
    """
    Service for generating analytics and reports.
    
    Provides:
    - Sales summaries and trends
    - Top-selling products
    - Revenue analytics
    - Customer analytics
    - Inventory reports
    """
    
    @classmethod
    def get_sales_summary(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> SalesSummary:
        """
        Get sales summary for a period.
        
        Args:
            start_date: Period start (defaults to 30 days ago)
            end_date: Period end (defaults to now)
            
        Returns:
            SalesSummary with aggregated data
        """
        from apps.orders.models import Order, OrderStatus, PaymentStatus
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get paid orders in the period
        orders = Order.objects.filter(
            payment_status=PaymentStatus.PAID,
            paid_at__gte=start_date,
            paid_at__lte=end_date,
        )
        
        # Aggregate metrics
        stats = orders.aggregate(
            total_revenue=Sum("total"),
            total_orders=Count("id"),
            avg_order_value=Avg("total"),
            unique_customers=Count("customer", distinct=True),
        )
        
        # Get items sold
        items_sold = orders.aggregate(
            total_items=Sum("items__quantity"),
        )["total_items"] or 0
        
        return SalesSummary(
            period_start=start_date,
            period_end=end_date,
            total_revenue=stats["total_revenue"] or Decimal("0.00"),
            total_orders=stats["total_orders"] or 0,
            average_order_value=stats["avg_order_value"] or Decimal("0.00"),
            total_items_sold=items_sold,
            unique_customers=stats["unique_customers"] or 0,
        )
    
    @classmethod
    def get_sales_trend(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
        granularity: str = "day",
    ) -> List[Dict[str, Any]]:
        """
        Get sales trend over time.
        
        Args:
            start_date: Period start
            end_date: Period end
            granularity: 'day', 'week', or 'month'
            
        Returns:
            List of data points with date and metrics
        """
        from apps.orders.models import Order, PaymentStatus
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Choose truncation function
        if granularity == "week":
            trunc_fn = TruncWeek("paid_at")
        elif granularity == "month":
            trunc_fn = TruncMonth("paid_at")
        else:
            trunc_fn = TruncDate("paid_at")
        
        # Query with aggregation
        trend = (
            Order.objects.filter(
                payment_status=PaymentStatus.PAID,
                paid_at__gte=start_date,
                paid_at__lte=end_date,
            )
            .annotate(period=trunc_fn)
            .values("period")
            .annotate(
                revenue=Sum("total"),
                orders=Count("id"),
                avg_value=Avg("total"),
            )
            .order_by("period")
        )
        
        return [
            {
                "date": item["period"].isoformat() if item["period"] else None,
                "revenue": str(item["revenue"] or 0),
                "orders": item["orders"],
                "average_order_value": str(item["avg_value"] or 0),
            }
            for item in trend
        ]
    
    @classmethod
    def get_top_products(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 10,
        by: str = "revenue",
    ) -> List[TopProduct]:
        """
        Get top-selling products.
        
        Args:
            start_date: Period start
            end_date: Period end
            limit: Number of products to return
            by: 'revenue' or 'units'
            
        Returns:
            List of TopProduct
        """
        from apps.orders.models import OrderItem, PaymentStatus
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Query order items from paid orders
        items = (
            OrderItem.objects.filter(
                order__payment_status=PaymentStatus.PAID,
                order__paid_at__gte=start_date,
                order__paid_at__lte=end_date,
                product_id__isnull=False,
            )
            .values("product_id", "name")
            .annotate(
                units_sold=Sum("quantity"),
                revenue=Sum(F("unit_price") * F("quantity")),
            )
        )
        
        # Sort by chosen metric
        if by == "units":
            items = items.order_by("-units_sold")
        else:
            items = items.order_by("-revenue")
        
        items = items[:limit]
        
        return [
            TopProduct(
                product_id=str(item["product_id"]),
                product_name=item["name"],
                units_sold=item["units_sold"],
                revenue=item["revenue"] or Decimal("0.00"),
            )
            for item in items
        ]
    
    @classmethod
    def get_top_categories(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top-selling categories.
        """
        from apps.orders.models import OrderItem, PaymentStatus
        from apps.products.models import Product
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get product IDs from orders
        product_ids = OrderItem.objects.filter(
            order__payment_status=PaymentStatus.PAID,
            order__paid_at__gte=start_date,
            order__paid_at__lte=end_date,
            product_id__isnull=False,
        ).values_list("product_id", flat=True)
        
        # Get category distribution
        categories = (
            Product.objects.filter(id__in=product_ids)
            .values("category__id", "category__name", "category__slug")
            .annotate(product_count=Count("id"))
            .order_by("-product_count")[:limit]
        )
        
        return [
            {
                "category_id": str(cat["category__id"]),
                "category_name": cat["category__name"],
                "category_slug": cat["category__slug"],
                "products_sold": cat["product_count"],
            }
            for cat in categories
        ]
    
    @classmethod
    def get_inventory_report(cls) -> Dict[str, Any]:
        """
        Get inventory status report.
        
        Returns:
            Dict with inventory metrics and alerts
        """
        from apps.products.models import Product
        
        # Get inventory stats
        products = Product.objects.filter(is_active=True, track_inventory=True)
        
        total_products = products.count()
        in_stock = products.filter(stock_quantity__gt=0).count()
        out_of_stock = products.filter(stock_quantity=0).count()
        low_stock = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F("low_stock_threshold"),
        ).count()
        
        # Get low stock items
        low_stock_items = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F("low_stock_threshold"),
        ).values(
            "id", "name", "sku", "stock_quantity", "low_stock_threshold"
        )[:20]
        
        # Get out of stock items
        out_of_stock_items = products.filter(
            stock_quantity=0
        ).values("id", "name", "sku")[:20]
        
        # Calculate inventory value
        total_value = products.aggregate(
            value=Sum(F("stock_quantity") * F("price"))
        )["value"] or Decimal("0.00")
        
        return {
            "summary": {
                "total_tracked_products": total_products,
                "in_stock": in_stock,
                "out_of_stock": out_of_stock,
                "low_stock": low_stock,
                "total_inventory_value": str(total_value),
            },
            "alerts": {
                "low_stock_items": [
                    {
                        "id": str(item["id"]),
                        "name": item["name"],
                        "sku": item["sku"],
                        "current_stock": item["stock_quantity"],
                        "threshold": item["low_stock_threshold"],
                    }
                    for item in low_stock_items
                ],
                "out_of_stock_items": [
                    {
                        "id": str(item["id"]),
                        "name": item["name"],
                        "sku": item["sku"],
                    }
                    for item in out_of_stock_items
                ],
            },
        }
    
    @classmethod
    def get_customer_analytics(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """
        Get customer analytics.
        
        Returns:
            Dict with customer metrics
        """
        from apps.orders.models import Order, PaymentStatus
        from apps.authentication.models import User
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # New customers in period
        new_customers = User.objects.filter(
            date_joined__gte=start_date,
            date_joined__lte=end_date,
        ).count()
        
        # Customers who made purchases
        paying_customers = Order.objects.filter(
            payment_status=PaymentStatus.PAID,
            paid_at__gte=start_date,
            paid_at__lte=end_date,
        ).values("customer").distinct().count()
        
        # Repeat customers (more than one order ever)
        repeat_customers = (
            Order.objects.filter(
                payment_status=PaymentStatus.PAID,
            )
            .values("customer")
            .annotate(order_count=Count("id"))
            .filter(order_count__gt=1)
            .count()
        )
        
        # Top customers by revenue
        top_customers = (
            Order.objects.filter(
                payment_status=PaymentStatus.PAID,
                paid_at__gte=start_date,
                paid_at__lte=end_date,
                customer__isnull=False,
            )
            .values("customer__id", "customer__email", "customer__first_name", "customer__last_name")
            .annotate(
                total_spent=Sum("total"),
                order_count=Count("id"),
            )
            .order_by("-total_spent")[:10]
        )
        
        return {
            "summary": {
                "new_customers": new_customers,
                "paying_customers": paying_customers,
                "repeat_customers": repeat_customers,
            },
            "top_customers": [
                {
                    "id": str(c["customer__id"]),
                    "email": c["customer__email"],
                    "name": f"{c['customer__first_name']} {c['customer__last_name']}".strip() or c["customer__email"],
                    "total_spent": str(c["total_spent"]),
                    "order_count": c["order_count"],
                }
                for c in top_customers
            ],
        }
    
    @classmethod
    def get_booking_analytics(
        cls,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Dict[str, Any]:
        """
        Get booking/service analytics.
        
        Returns:
            Dict with booking metrics
        """
        from apps.bookings.models import Booking
        
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        bookings = Booking.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
        )
        
        stats = bookings.aggregate(
            total_bookings=Count("id"),
            confirmed_bookings=Count("id", filter=Q(status="confirmed")),
            completed_bookings=Count("id", filter=Q(status="completed")),
            cancelled_bookings=Count("id", filter=Q(status="cancelled")),
            total_revenue=Sum("total_price", filter=Q(status="completed")),
        )
        
        # Top services by bookings
        top_services = (
            bookings
            .values("service__id", "service__name")
            .annotate(
                booking_count=Count("id"),
                revenue=Sum("total_price", filter=Q(status="completed")),
            )
            .order_by("-booking_count")[:10]
        )
        
        return {
            "summary": {
                "total_bookings": stats["total_bookings"] or 0,
                "confirmed_bookings": stats["confirmed_bookings"] or 0,
                "completed_bookings": stats["completed_bookings"] or 0,
                "cancelled_bookings": stats["cancelled_bookings"] or 0,
                "total_revenue": str(stats["total_revenue"] or 0),
            },
            "top_services": [
                {
                    "id": str(s["service__id"]),
                    "name": s["service__name"],
                    "booking_count": s["booking_count"],
                    "revenue": str(s["revenue"] or 0),
                }
                for s in top_services
            ],
        }
    
    @classmethod
    def get_dashboard_summary(cls) -> Dict[str, Any]:
        """
        Get a comprehensive dashboard summary.
        
        Returns:
            Dict with all key metrics for dashboard
        """
        now = timezone.now()
        
        # Current period (last 30 days)
        current_start = now - timedelta(days=30)
        current_summary = cls.get_sales_summary(current_start, now)
        
        # Previous period (30-60 days ago)
        previous_start = now - timedelta(days=60)
        previous_end = now - timedelta(days=30)
        previous_summary = cls.get_sales_summary(previous_start, previous_end)
        
        # Calculate changes
        def calc_change(current, previous):
            if not previous or previous == 0:
                return None
            return round(((current - previous) / previous) * 100, 1)
        
        revenue_change = calc_change(
            float(current_summary.total_revenue),
            float(previous_summary.total_revenue),
        )
        orders_change = calc_change(
            current_summary.total_orders,
            previous_summary.total_orders,
        )
        
        # Get other summaries
        inventory = cls.get_inventory_report()
        
        return {
            "sales": {
                "revenue": str(current_summary.total_revenue),
                "revenue_change": revenue_change,
                "orders": current_summary.total_orders,
                "orders_change": orders_change,
                "average_order_value": str(current_summary.average_order_value),
                "items_sold": current_summary.total_items_sold,
                "unique_customers": current_summary.unique_customers,
            },
            "inventory": inventory["summary"],
            "alerts": {
                "low_stock_count": len(inventory["alerts"]["low_stock_items"]),
                "out_of_stock_count": len(inventory["alerts"]["out_of_stock_items"]),
            },
            "recent_trend": cls.get_sales_trend(now - timedelta(days=7), now, "day"),
            "top_products": [p.to_dict() for p in cls.get_top_products(limit=5)],
        }
