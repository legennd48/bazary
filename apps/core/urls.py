"""
Core app URLs for health checks and utilities.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.health_check, name="health-check"),
]
