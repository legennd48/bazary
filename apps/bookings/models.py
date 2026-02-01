"""
Booking Models.

Time-based reservation system with availability management.
"""

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel


class DayOfWeek(models.IntegerChoices):
    """Days of the week (ISO 8601: Monday = 1)."""
    MONDAY = 1, "Monday"
    TUESDAY = 2, "Tuesday"
    WEDNESDAY = 3, "Wednesday"
    THURSDAY = 4, "Thursday"
    FRIDAY = 5, "Friday"
    SATURDAY = 6, "Saturday"
    SUNDAY = 7, "Sunday"


class BookingStatus(models.TextChoices):
    """Booking lifecycle status."""
    PENDING = "pending", "Pending Confirmation"
    CONFIRMED = "confirmed", "Confirmed"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    NO_SHOW = "no_show", "No Show"
    RESCHEDULED = "rescheduled", "Rescheduled"


class CancellationReason(models.TextChoices):
    """Common cancellation reasons."""
    CUSTOMER_REQUEST = "customer_request", "Customer Request"
    PROVIDER_UNAVAILABLE = "provider_unavailable", "Provider Unavailable"
    SCHEDULE_CONFLICT = "schedule_conflict", "Schedule Conflict"
    WEATHER = "weather", "Weather"
    EMERGENCY = "emergency", "Emergency"
    NO_SHOW = "no_show", "No Show"
    OTHER = "other", "Other"


class AvailabilitySchedule(TimeStampedModel):
    """
    Recurring availability schedule for a service provider.
    
    Defines when a provider is generally available to work.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Can be provider-specific or service-specific
    provider = models.ForeignKey(
        "services.ServiceProvider",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="availability_schedules",
        help_text="Provider this schedule applies to",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="availability_schedules",
        help_text="Service this schedule applies to (if no provider specified)",
    )
    
    name = models.CharField(
        max_length=100,
        default="Default Schedule",
        help_text="Schedule name for management",
    )
    
    # Effective date range
    effective_from = models.DateField(
        null=True,
        blank=True,
        help_text="When this schedule starts (null = always)",
    )
    effective_until = models.DateField(
        null=True,
        blank=True,
        help_text="When this schedule ends (null = indefinite)",
    )
    
    is_active = models.BooleanField(
        default=True,
    )
    
    class Meta:
        db_table = "availability_schedules"
        ordering = ["-is_active", "name"]
    
    def __str__(self):
        if self.provider:
            return f"{self.provider.user.get_full_name()} - {self.name}"
        if self.service:
            return f"{self.service.name} - {self.name}"
        return self.name
    
    def clean(self):
        if not self.provider and not self.service:
            raise ValidationError(
                "Schedule must be associated with a provider or service"
            )
    
    def is_effective_on(self, check_date: date) -> bool:
        """Check if schedule is effective on a given date."""
        if not self.is_active:
            return False
        if self.effective_from and check_date < self.effective_from:
            return False
        if self.effective_until and check_date > self.effective_until:
            return False
        return True


class AvailabilitySlot(TimeStampedModel):
    """
    Time slots within an availability schedule.
    
    Defines specific hours available on specific days.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    schedule = models.ForeignKey(
        AvailabilitySchedule,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    
    day_of_week = models.PositiveSmallIntegerField(
        choices=DayOfWeek.choices,
        help_text="Day of week (1=Monday, 7=Sunday)",
    )
    
    start_time = models.TimeField(
        help_text="Slot start time",
    )
    end_time = models.TimeField(
        help_text="Slot end time",
    )
    
    class Meta:
        db_table = "availability_slots"
        ordering = ["day_of_week", "start_time"]
        unique_together = ["schedule", "day_of_week", "start_time"]
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")
    
    @property
    def duration_minutes(self) -> int:
        """Calculate slot duration in minutes."""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)


class BlockedTime(TimeStampedModel):
    """
    Time blocks when provider/service is unavailable.
    
    For vacations, holidays, breaks, etc.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    provider = models.ForeignKey(
        "services.ServiceProvider",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blocked_times",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blocked_times",
    )
    
    title = models.CharField(
        max_length=100,
        help_text="Reason for block (e.g., 'Vacation', 'Lunch Break')",
    )
    
    start_datetime = models.DateTimeField(
        help_text="Block start time",
    )
    end_datetime = models.DateTimeField(
        help_text="Block end time",
    )
    
    is_all_day = models.BooleanField(
        default=False,
        help_text="Whether this blocks the entire day",
    )
    
    is_recurring = models.BooleanField(
        default=False,
        help_text="Whether this block repeats",
    )
    recurrence_rule = models.CharField(
        max_length=255,
        blank=True,
        help_text="iCal RRULE string for recurring blocks",
    )
    
    class Meta:
        db_table = "blocked_times"
        ordering = ["start_datetime"]
    
    def __str__(self):
        return f"{self.title} ({self.start_datetime} - {self.end_datetime})"
    
    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("End time must be after start time")
        if not self.provider and not self.service:
            raise ValidationError(
                "Blocked time must be associated with a provider or service"
            )


class Booking(TimeStampedModel):
    """
    Core booking model.
    
    Represents a time reservation for a service.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Reference number (human readable)
    reference = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Human-readable booking reference",
    )
    
    # What
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text="Service being booked",
    )
    
    # Who provides
    provider = models.ForeignKey(
        "services.ServiceProvider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        help_text="Provider assigned to this booking",
    )
    
    # Who booked
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text="Customer who made the booking",
    )
    
    # When
    start_datetime = models.DateTimeField(
        db_index=True,
        help_text="Booking start time",
    )
    end_datetime = models.DateTimeField(
        db_index=True,
        help_text="Booking end time",
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True,
    )
    
    # Attendees (for group services)
    attendee_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of attendees",
    )
    attendee_names = models.JSONField(
        default=list,
        blank=True,
        help_text="List of attendee names for group bookings",
    )
    
    # Pricing at time of booking
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Price per attendee at booking time",
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total booking price",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
    )
    
    # Add-ons
    addons = models.JSONField(
        default=list,
        blank=True,
        help_text="List of add-on IDs and prices at booking time",
    )
    
    # Customer notes
    customer_notes = models.TextField(
        blank=True,
        help_text="Notes from customer",
    )
    
    # Internal notes
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal staff notes",
    )
    
    # Confirmation
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_bookings",
    )
    
    # Cancellation
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_bookings",
    )
    cancellation_reason = models.CharField(
        max_length=30,
        choices=CancellationReason.choices,
        blank=True,
    )
    cancellation_notes = models.TextField(
        blank=True,
    )
    
    # Completion
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    # Link to order (if payment required)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    
    # Rescheduling
    rescheduled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_to",
        help_text="Original booking if this is a reschedule",
    )
    
    # Reminder tracking
    reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    class Meta:
        db_table = "bookings"
        ordering = ["-start_datetime"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["provider", "start_datetime"]),
            models.Index(fields=["service", "start_datetime"]),
            models.Index(fields=["status", "start_datetime"]),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.service.name}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)
    
    def _generate_reference(self) -> str:
        """Generate unique booking reference."""
        import random
        import string
        
        # Format: BK-YYYYMMDD-XXXX
        date_part = timezone.now().strftime("%Y%m%d")
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"BK-{date_part}-{random_part}"
    
    @property
    def duration_minutes(self) -> int:
        """Calculate booking duration in minutes."""
        return int((self.end_datetime - self.start_datetime).total_seconds() / 60)
    
    @property
    def is_upcoming(self) -> bool:
        """Check if booking is in the future."""
        return self.start_datetime > timezone.now()
    
    @property
    def is_cancellable(self) -> bool:
        """Check if booking can be cancelled."""
        if self.status in [
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.NO_SHOW,
        ]:
            return False
        
        # Check minimum notice
        hours_until = (self.start_datetime - timezone.now()).total_seconds() / 3600
        return hours_until >= self.service.min_notice_hours
    
    @property
    def is_free_cancellation(self) -> bool:
        """Check if cancellation would be free."""
        if not self.is_cancellable:
            return False
        
        hours_until = (self.start_datetime - timezone.now()).total_seconds() / 3600
        return hours_until >= self.service.free_cancellation_hours
    
    def confirm(self, user=None):
        """Confirm the booking."""
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        self.confirmed_by = user
        self.save(update_fields=["status", "confirmed_at", "confirmed_by", "updated_at"])
    
    def cancel(self, user=None, reason="", notes=""):
        """Cancel the booking."""
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        self.save(update_fields=[
            "status",
            "cancelled_at",
            "cancelled_by",
            "cancellation_reason",
            "cancellation_notes",
            "updated_at",
        ])
    
    def complete(self):
        """Mark booking as completed."""
        self.status = BookingStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
    
    def mark_no_show(self):
        """Mark customer as no-show."""
        self.status = BookingStatus.NO_SHOW
        self.save(update_fields=["status", "updated_at"])


class BookingStatusHistory(TimeStampedModel):
    """
    Track booking status changes.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    
    from_status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        blank=True,
    )
    to_status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    notes = models.TextField(
        blank=True,
    )
    
    class Meta:
        db_table = "booking_status_history"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.booking.reference}: {self.from_status} → {self.to_status}"
