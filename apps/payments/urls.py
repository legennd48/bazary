"""
Payment URL configuration with nested routing support.

This module defines URL patterns for all payment-related endpoints including:
- Payment providers
- Payment methods
- Transactions
- Shopping carts
- Cart items (with nested routing)
- Webhook endpoints
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    CartItemViewSet,
    CartViewSet,
    PaymentMethodViewSet,
    PaymentProviderViewSet,
    TransactionViewSet,
)
from .webhooks import (
    ChapaWebhookView,
    chapa_webhook_api,
    verify_payment_callback,
)

app_name = "payments"

# Main router for top-level resources
router = DefaultRouter()
router.register(r"providers", PaymentProviderViewSet, basename="provider")
router.register(r"methods", PaymentMethodViewSet, basename="method")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"carts", CartViewSet, basename="cart")

# Nested router for cart items
carts_router = routers.NestedDefaultRouter(router, r"carts", lookup="cart")
carts_router.register(r"items", CartItemViewSet, basename="cart-items")

# URL patterns - Use simple approach to avoid router conflicts
urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    # Include nested cart item routes (this will create some duplication but it's harmless)
    path("", include(carts_router.urls)),
    # Webhook endpoints
    path("webhooks/chapa/", ChapaWebhookView.as_view(), name="chapa-webhook"),
    path("webhooks/chapa/api/", chapa_webhook_api, name="chapa-webhook-api"),
    path("callbacks/verify/", verify_payment_callback, name="payment-verify-callback"),
]
