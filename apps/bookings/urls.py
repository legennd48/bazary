"""
Booking URL routing.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AvailabilityScheduleViewSet,
    AvailabilityView,
    BlockedTimeViewSet,
    BookingViewSet,
)

app_name = "bookings"

router = DefaultRouter()
router.register("schedules", AvailabilityScheduleViewSet, basename="schedule")
router.register("blocked", BlockedTimeViewSet, basename="blocked")
router.register("", BookingViewSet, basename="booking")

urlpatterns = [
    path("availability/", AvailabilityView.as_view(), name="availability"),
    path("", include(router.urls)),
]
