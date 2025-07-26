"""
Products app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.ProductViewSet, basename='product')
router.register('tags', views.TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
