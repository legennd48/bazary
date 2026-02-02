"""
Wishlist URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views.wishlist import WishlistViewSet

router = DefaultRouter()
router.register("", WishlistViewSet, basename="wishlist")

urlpatterns = [
    path("", include(router.urls)),
]
