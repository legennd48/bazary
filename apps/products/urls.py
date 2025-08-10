"""
Enhanced Products app URLs with variant management.
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (
    ProductManagementViewSet,
    ProductVariantViewSet,
    ProductViewSet,
    TagViewSet,
    VariantOptionValueViewSet,
    VariantOptionViewSet,
)

# Create router and register all viewsets
router = DefaultRouter()

# Core product management
router.register(r"products", ProductViewSet, basename="product")
router.register(r"tags", TagViewSet, basename="tag")

# Advanced product management
router.register(r"management", ProductManagementViewSet, basename="product-management")

# Variant management
router.register(r"variant-options", VariantOptionViewSet, basename="variant-option")
router.register(
    r"variant-option-values", VariantOptionValueViewSet, basename="variant-option-value"
)
router.register(r"variants", ProductVariantViewSet, basename="product-variant")

urlpatterns = [
    path("", include(router.urls)),
]
