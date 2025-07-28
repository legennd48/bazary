"""
Products app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create separate routers to avoid conflicts
product_router = DefaultRouter()
product_router.register('', views.ProductViewSet, basename='product')

tag_router = DefaultRouter() 
tag_router.register('', views.TagViewSet, basename='tag')

urlpatterns = [
    # Products at root level
    path('', include(product_router.urls)),
    # Tags at /tags/ level  
    path('tags/', include(tag_router.urls)),
]
