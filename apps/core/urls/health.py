"""
Core app URLs for health checks and utilities.
"""

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.health_check, name="health-check"),
]
