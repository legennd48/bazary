"""
Notification URL routing.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationPreferenceView, NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [
    path("preferences/", NotificationPreferenceView.as_view(), name="preferences"),
    path("", include(router.urls)),
]
