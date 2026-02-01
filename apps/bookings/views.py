"""
Booking Views.

ViewSets for booking management with availability checking.
"""

from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.capabilities.registry import require_capability
from apps.services.models import Service, ServiceProvider

from .models import (
    AvailabilitySchedule,
    BlockedTime,
    Booking,
    BookingStatus,
)
from .serializers import (
    AvailabilityQuerySerializer,
    AvailabilityScheduleCreateSerializer,
    AvailabilityScheduleDetailSerializer,
    AvailabilityScheduleListSerializer,
    AvailableSlotSerializer,
    BlockedTimeSerializer,
    BookingCancelSerializer,
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    BookingRescheduleSerializer,
)
from .services import AvailabilityEngine, BookingService


class AvailabilityScheduleFilter(filters.FilterSet):
    """Filters for availability schedules."""
    
    provider = filters.UUIDFilter(field_name="provider_id")
    service = filters.UUIDFilter(field_name="service_id")
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = AvailabilitySchedule
        fields = ["provider", "service", "is_active"]


@require_capability("bookings")
class AvailabilityScheduleViewSet(viewsets.ModelViewSet):
    """
    CRUD for availability schedules.
    
    Endpoints:
    - GET /schedules/ - List schedules (admin)
    - POST /schedules/ - Create schedule (admin)
    - GET /schedules/{id}/ - Get schedule details (admin)
    - PATCH /schedules/{id}/ - Update schedule (admin)
    - DELETE /schedules/{id}/ - Delete schedule (admin)
    """
    
    queryset = AvailabilitySchedule.objects.all()
    filterset_class = AvailabilityScheduleFilter
    permission_classes = [IsAdminUser]
    lookup_field = "id"
    
    def get_serializer_class(self):
        if self.action == "list":
            return AvailabilityScheduleListSerializer
        if self.action == "retrieve":
            return AvailabilityScheduleDetailSerializer
        return AvailabilityScheduleCreateSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "provider__user",
            "service",
        ).prefetch_related("slots")


@require_capability("bookings")
class BlockedTimeViewSet(viewsets.ModelViewSet):
    """
    CRUD for blocked time periods.
    
    Endpoints:
    - GET /blocked/ - List blocked times (admin)
    - POST /blocked/ - Create blocked time (admin)
    - GET /blocked/{id}/ - Get blocked time details (admin)
    - PATCH /blocked/{id}/ - Update blocked time (admin)
    - DELETE /blocked/{id}/ - Delete blocked time (admin)
    """
    
    queryset = BlockedTime.objects.all()
    serializer_class = BlockedTimeSerializer
    permission_classes = [IsAdminUser]
    lookup_field = "id"
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by provider or service
        provider_id = self.request.query_params.get("provider")
        service_id = self.request.query_params.get("service")
        
        if provider_id:
            qs = qs.filter(provider_id=provider_id)
        if service_id:
            qs = qs.filter(service_id=service_id)
        
        # Filter by date range
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        
        if start:
            qs = qs.filter(end_datetime__gte=start)
        if end:
            qs = qs.filter(start_datetime__lte=end)
        
        return qs.select_related("provider__user", "service")


class BookingFilter(filters.FilterSet):
    """Filters for bookings."""
    
    service = filters.UUIDFilter(field_name="service_id")
    provider = filters.UUIDFilter(field_name="provider_id")
    customer = filters.UUIDFilter(field_name="customer_id")
    status = filters.ChoiceFilter(choices=BookingStatus.choices)
    reference = filters.CharFilter(lookup_expr="icontains")
    start_date = filters.DateFilter(field_name="start_datetime", lookup_expr="date__gte")
    end_date = filters.DateFilter(field_name="start_datetime", lookup_expr="date__lte")
    upcoming = filters.BooleanFilter(method="filter_upcoming")
    
    class Meta:
        model = Booking
        fields = ["service", "provider", "customer", "status", "reference"]
    
    def filter_upcoming(self, queryset, name, value):
        if value:
            return queryset.filter(start_datetime__gt=timezone.now())
        return queryset.filter(start_datetime__lte=timezone.now())


@require_capability("bookings")
class BookingViewSet(viewsets.ModelViewSet):
    """
    Booking management.
    
    Endpoints:
    - GET /bookings/ - List bookings
    - POST /bookings/ - Create booking
    - GET /bookings/{id}/ - Get booking details
    - PATCH /bookings/{id}/ - Update booking (admin)
    - DELETE /bookings/{id}/ - Delete booking (admin)
    - POST /bookings/{id}/confirm/ - Confirm booking (admin)
    - POST /bookings/{id}/cancel/ - Cancel booking
    - POST /bookings/{id}/reschedule/ - Reschedule booking
    - POST /bookings/{id}/complete/ - Mark completed (admin)
    - POST /bookings/{id}/no-show/ - Mark no-show (admin)
    """
    
    queryset = Booking.objects.all()
    filterset_class = BookingFilter
    lookup_field = "id"
    
    def get_permissions(self):
        if self.action in ["list", "retrieve", "create", "cancel", "reschedule"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == "list":
            return BookingListSerializer
        if self.action == "create":
            return BookingCreateSerializer
        if self.action == "cancel":
            return BookingCancelSerializer
        if self.action == "reschedule":
            return BookingRescheduleSerializer
        return BookingDetailSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Non-admins can only see their own bookings
        if not self.request.user.is_staff:
            qs = qs.filter(customer=self.request.user)
        
        if self.action == "list":
            return qs.select_related(
                "service",
                "provider__user",
                "customer",
            )
        
        if self.action == "retrieve":
            return qs.select_related(
                "service__category",
                "provider__user",
                "customer",
                "confirmed_by",
                "cancelled_by",
                "rescheduled_from",
            ).prefetch_related("status_history__changed_by")
        
        return qs
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            service = Service.objects.get(id=data["service_id"])
            provider = None
            
            if data.get("provider_id"):
                provider = ServiceProvider.objects.get(id=data["provider_id"])
            
            booking = BookingService.create_booking(
                service=service,
                customer=request.user,
                start_datetime=data["start_datetime"],
                provider=provider,
                attendee_count=data.get("attendee_count", 1),
                attendee_names=data.get("attendee_names", []),
                addon_ids=data.get("addon_ids", []),
                customer_notes=data.get("customer_notes", ""),
            )
            
            return Response(
                BookingDetailSerializer(booking).data,
                status=status.HTTP_201_CREATED,
            )
        
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"])
    def confirm(self, request, id=None):
        """Confirm a pending booking."""
        booking = self.get_object()
        
        try:
            BookingService.confirm_booking(booking, request.user)
            return Response(BookingDetailSerializer(booking).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"])
    def cancel(self, request, id=None):
        """Cancel a booking."""
        booking = self.get_object()
        
        # Non-admins can only cancel their own bookings
        if not request.user.is_staff and booking.customer != request.user:
            return Response(
                {"detail": "You can only cancel your own bookings"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = BookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            BookingService.cancel_booking(
                booking,
                request.user,
                serializer.validated_data.get("reason", ""),
                serializer.validated_data.get("notes", ""),
            )
            return Response(BookingDetailSerializer(booking).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"])
    def reschedule(self, request, id=None):
        """Reschedule a booking."""
        booking = self.get_object()
        
        # Non-admins can only reschedule their own bookings
        if not request.user.is_staff and booking.customer != request.user:
            return Response(
                {"detail": "You can only reschedule your own bookings"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = BookingRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            new_provider = None
            if serializer.validated_data.get("new_provider_id"):
                new_provider = ServiceProvider.objects.get(
                    id=serializer.validated_data["new_provider_id"]
                )
            
            new_booking = BookingService.reschedule_booking(
                booking,
                serializer.validated_data["new_start_datetime"],
                new_provider,
                request.user,
            )
            
            return Response(
                BookingDetailSerializer(new_booking).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"])
    def complete(self, request, id=None):
        """Mark booking as completed."""
        booking = self.get_object()
        
        try:
            BookingService.complete_booking(booking)
            return Response(BookingDetailSerializer(booking).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=["post"], url_path="no-show")
    def no_show(self, request, id=None):
        """Mark customer as no-show."""
        booking = self.get_object()
        
        try:
            BookingService.mark_no_show(booking, request.user)
            return Response(BookingDetailSerializer(booking).data)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@require_capability("bookings")
class AvailabilityView(APIView):
    """
    Check available booking slots.
    
    GET /availability/?service_id=...&start_date=...&end_date=...
    """
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            service = Service.objects.get(id=data["service_id"])
        except Service.DoesNotExist:
            return Response(
                {"detail": "Service not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        provider = None
        if data.get("provider_id"):
            try:
                provider = ServiceProvider.objects.get(id=data["provider_id"])
            except ServiceProvider.DoesNotExist:
                return Response(
                    {"detail": "Provider not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        
        engine = AvailabilityEngine(service)
        slots = engine.get_available_slots(
            start_date=data["start_date"],
            end_date=data["end_date"],
            provider=provider,
            slot_interval_minutes=data.get("slot_interval", 30),
        )
        
        return Response({
            "service_id": str(service.id),
            "service_name": service.name,
            "duration_minutes": service.total_duration_minutes,
            "slots": [slot.to_dict() for slot in slots],
            "slot_count": len(slots),
        })
