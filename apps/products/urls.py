"""
Products app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Products router only
router = DefaultRouter()
router.register("", views.ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]
