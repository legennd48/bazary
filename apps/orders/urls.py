"""
Order URLs.
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import CheckoutViewSet, OrderViewSet

app_name = "orders"

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="orders")

urlpatterns = [
    path("checkout/", CheckoutViewSet.as_view({"post": "create"}), name="checkout"),
    path("checkout/validate/", CheckoutViewSet.as_view({"post": "validate"}), name="checkout-validate"),
    path("", include(router.urls)),
]
