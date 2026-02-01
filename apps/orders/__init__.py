"""
Orders Domain App.

This app handles the complete order lifecycle:
- Cart to checkout conversion
- Order creation and management
- Order items with product/variant/service references
- Order status workflow (Shopify-like clarity)
- Fulfillment tracking
- Refunds and cancellations

The Orders domain is the canonical record of commerce - it ties
together products, services, bookings, and payments.
"""

default_app_config = "apps.orders.apps.OrdersConfig"
