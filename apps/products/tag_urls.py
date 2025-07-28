"""
Tag URLs - separated for clean API structure.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Tags router
router = DefaultRouter()
router.register('', views.TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
