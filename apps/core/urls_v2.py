"""
Core API v2 URLs for platform information and capabilities.

These endpoints help frontends understand what capabilities
are available and how to configure their UI accordingly.
"""

from django.urls import path

from .views import (
    PlatformCapabilitiesView,
    PlatformConfigView,
    PlatformHealthView,
)

app_name = "platform"

urlpatterns = [
    path("capabilities/", PlatformCapabilitiesView.as_view(), name="capabilities"),
    path("config/", PlatformConfigView.as_view(), name="config"),
    path("health/", PlatformHealthView.as_view(), name="health"),
]
