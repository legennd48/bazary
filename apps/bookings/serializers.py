"""
Booking Serializers.

Full serializer set for booking API operations.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.services.models import Service, ServiceProvider
from apps.services.serializers import ServiceListSerializer, ServiceProviderMinimalSerializer

from .models import (
    AvailabilitySchedule,
    AvailabilitySlot,
    BlockedTime,
    Booking,
    BookingStatus,
    BookingStatusHistory,
    CancellationReason,
    DayOfWeek,
)


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    """Availability slot within a schedule."""
    
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = AvailabilitySlot
        fields = [
            "id",
            "day_of_week",
            "day_name",
            "start_time",
            "end_time",
            "duration_minutes",
        ]
        read_only_fields = ["id"]
    
    def validate(self, attrs):
        if attrs.get("start_time") and attrs.get("end_time"):
            if attrs["start_time"] >= attrs["end_time"]:
                raise serializers.ValidationError({
                    "end_time": "End time must be after start time"
                })
        return attrs


class AvailabilityScheduleListSerializer(serializers.ModelSerializer):
    """Minimal schedule info for lists."""
    
    provider_name = serializers.CharField(
        source="provider.user.get_full_name",
        read_only=True,
    )
    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
    )
    slot_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AvailabilitySchedule
        fields = [
            "id",
            "name",
            "provider",
            "provider_name",
            "service",
            "service_name",
            "effective_from",
            "effective_until",
            "is_active",
            "slot_count",
        ]
    
    def get_slot_count(self, obj) -> int:
        return obj.slots.count()


class AvailabilityScheduleDetailSerializer(serializers.ModelSerializer):
    """Full schedule details with slots."""
    
    slots = AvailabilitySlotSerializer(many=True, read_only=True)
    provider_name = serializers.CharField(
        source="provider.user.get_full_name",
        read_only=True,
    )
    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
    )
    
    class Meta:
        model = AvailabilitySchedule
        fields = [
            "id",
            "name",
            "provider",
            "provider_name",
            "service",
            "service_name",
            "effective_from",
            "effective_until",
            "is_active",
            "slots",
            "created_at",
            "updated_at",
        ]


class AvailabilityScheduleCreateSerializer(serializers.ModelSerializer):
    """Create/update schedule."""
    
    slots = AvailabilitySlotSerializer(many=True, required=False)
    
    class Meta:
        model = AvailabilitySchedule
        fields = [
            "id",
            "name",
            "provider",
            "service",
            "effective_from",
            "effective_until",
            "is_active",
            "slots",
        ]
        read_only_fields = ["id"]
    
    def validate(self, attrs):
        provider = attrs.get("provider")
        service = attrs.get("service")
        
        if not provider and not service:
            raise serializers.ValidationError(
                "Either provider or service must be specified"
            )
        
        if attrs.get("effective_from") and attrs.get("effective_until"):
            if attrs["effective_from"] > attrs["effective_until"]:
                raise serializers.ValidationError({
                    "effective_until": "End date must be after start date"
                })
        
        return attrs
    
    def create(self, validated_data):
        slots_data = validated_data.pop("slots", [])
        schedule = AvailabilitySchedule.objects.create(**validated_data)
        
        for slot_data in slots_data:
            AvailabilitySlot.objects.create(schedule=schedule, **slot_data)
        
        return schedule
    
    def update(self, instance, validated_data):
        slots_data = validated_data.pop("slots", None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Replace slots if provided
        if slots_data is not None:
            instance.slots.all().delete()
            for slot_data in slots_data:
                AvailabilitySlot.objects.create(schedule=instance, **slot_data)
        
        return instance


class BlockedTimeSerializer(serializers.ModelSerializer):
    """Blocked time periods."""
    
    provider_name = serializers.CharField(
        source="provider.user.get_full_name",
        read_only=True,
    )
    service_name = serializers.CharField(
        source="service.name",
        read_only=True,
    )
    
    class Meta:
        model = BlockedTime
        fields = [
            "id",
            "provider",
            "provider_name",
            "service",
            "service_name",
            "title",
            "start_datetime",
            "end_datetime",
            "is_all_day",
            "is_recurring",
            "recurrence_rule",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
    
    def validate(self, attrs):
        if not attrs.get("provider") and not attrs.get("service"):
            raise serializers.ValidationError(
                "Either provider or service must be specified"
            )
        
        if attrs.get("start_datetime") and attrs.get("end_datetime"):
            if attrs["start_datetime"] >= attrs["end_datetime"]:
                raise serializers.ValidationError({
                    "end_datetime": "End time must be after start time"
                })
        
        return attrs


class AvailableSlotSerializer(serializers.Serializer):
    """Available time slot for booking."""
    
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    provider_id = serializers.UUIDField(allow_null=True)
    provider_name = serializers.CharField(allow_null=True)


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    """Booking status change history."""
    
    changed_by_email = serializers.EmailField(
        source="changed_by.email",
        read_only=True,
    )
    
    class Meta:
        model = BookingStatusHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_email",
            "notes",
            "created_at",
        ]


class BookingListSerializer(serializers.ModelSerializer):
    """Minimal booking info for lists."""
    
    service_name = serializers.CharField(source="service.name", read_only=True)
    provider_name = serializers.CharField(
        source="provider.user.get_full_name",
        read_only=True,
    )
    customer_name = serializers.CharField(
        source="customer.get_full_name",
        read_only=True,
    )
    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )
    duration_minutes = serializers.IntegerField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "service",
            "service_name",
            "provider",
            "provider_name",
            "customer",
            "customer_name",
            "customer_email",
            "start_datetime",
            "end_datetime",
            "duration_minutes",
            "status",
            "attendee_count",
            "total_price",
            "currency",
            "is_upcoming",
            "is_cancellable",
            "created_at",
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    """Full booking details."""
    
    service = ServiceListSerializer(read_only=True)
    provider = ServiceProviderMinimalSerializer(read_only=True)
    customer_name = serializers.CharField(
        source="customer.get_full_name",
        read_only=True,
    )
    customer_email = serializers.EmailField(
        source="customer.email",
        read_only=True,
    )
    duration_minutes = serializers.IntegerField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_cancellable = serializers.BooleanField(read_only=True)
    is_free_cancellation = serializers.BooleanField(read_only=True)
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)
    confirmed_by_email = serializers.EmailField(
        source="confirmed_by.email",
        read_only=True,
    )
    cancelled_by_email = serializers.EmailField(
        source="cancelled_by.email",
        read_only=True,
    )
    rescheduled_from_ref = serializers.CharField(
        source="rescheduled_from.reference",
        read_only=True,
    )
    
    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "service",
            "provider",
            "customer",
            "customer_name",
            "customer_email",
            "start_datetime",
            "end_datetime",
            "duration_minutes",
            "status",
            "attendee_count",
            "attendee_names",
            "unit_price",
            "total_price",
            "currency",
            "addons",
            "customer_notes",
            "internal_notes",
            "confirmed_at",
            "confirmed_by",
            "confirmed_by_email",
            "cancelled_at",
            "cancelled_by",
            "cancelled_by_email",
            "cancellation_reason",
            "cancellation_notes",
            "completed_at",
            "order",
            "rescheduled_from",
            "rescheduled_from_ref",
            "reminder_sent_at",
            "is_upcoming",
            "is_cancellable",
            "is_free_cancellation",
            "status_history",
            "created_at",
            "updated_at",
        ]


class BookingCreateSerializer(serializers.Serializer):
    """Create a new booking."""
    
    service_id = serializers.UUIDField()
    provider_id = serializers.UUIDField(required=False, allow_null=True)
    start_datetime = serializers.DateTimeField()
    attendee_count = serializers.IntegerField(default=1, min_value=1)
    attendee_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
    )
    addon_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    customer_notes = serializers.CharField(required=False, default="", allow_blank=True)
    
    def validate_service_id(self, value):
        try:
            Service.objects.get(id=value, status="active")
            return value
        except Service.DoesNotExist:
            raise serializers.ValidationError("Service not found or not active")
    
    def validate_provider_id(self, value):
        if value:
            try:
                ServiceProvider.objects.get(id=value, is_active=True)
                return value
            except ServiceProvider.DoesNotExist:
                raise serializers.ValidationError("Provider not found or not active")
        return value
    
    def validate_start_datetime(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Booking cannot be in the past")
        return value


class BookingRescheduleSerializer(serializers.Serializer):
    """Reschedule a booking."""
    
    new_start_datetime = serializers.DateTimeField()
    new_provider_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_new_start_datetime(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("New time cannot be in the past")
        return value
    
    def validate_new_provider_id(self, value):
        if value:
            try:
                ServiceProvider.objects.get(id=value, is_active=True)
                return value
            except ServiceProvider.DoesNotExist:
                raise serializers.ValidationError("Provider not found or not active")
        return value


class BookingCancelSerializer(serializers.Serializer):
    """Cancel a booking."""
    
    reason = serializers.ChoiceField(
        choices=CancellationReason.choices,
        required=False,
        default=CancellationReason.CUSTOMER_REQUEST,
    )
    notes = serializers.CharField(required=False, default="", allow_blank=True)


class AvailabilityQuerySerializer(serializers.Serializer):
    """Query parameters for availability check."""
    
    service_id = serializers.UUIDField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    provider_id = serializers.UUIDField(required=False)
    slot_interval = serializers.IntegerField(required=False, default=30, min_value=15)
    
    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        # Limit date range
        max_days = 60
        if (attrs["end_date"] - attrs["start_date"]).days > max_days:
            raise serializers.ValidationError({
                "end_date": f"Date range cannot exceed {max_days} days"
            })
        
        return attrs
