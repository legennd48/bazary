"""
Notification Models.

Persistent notification storage and event outbox pattern.
"""

import uuid
from typing import Any, Dict, Optional

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class NotificationType(models.TextChoices):
    """Types of notifications."""
    
    # Order events
    ORDER_CREATED = "order.created", "Order Created"
    ORDER_CONFIRMED = "order.confirmed", "Order Confirmed"
    ORDER_PAID = "order.paid", "Order Paid"
    ORDER_PROCESSING = "order.processing", "Order Processing"
    ORDER_SHIPPED = "order.shipped", "Order Shipped"
    ORDER_DELIVERED = "order.delivered", "Order Delivered"
    ORDER_CANCELLED = "order.cancelled", "Order Cancelled"
    ORDER_REFUNDED = "order.refunded", "Order Refunded"
    
    # Booking events
    BOOKING_CREATED = "booking.created", "Booking Created"
    BOOKING_CONFIRMED = "booking.confirmed", "Booking Confirmed"
    BOOKING_REMINDER = "booking.reminder", "Booking Reminder"
    BOOKING_CANCELLED = "booking.cancelled", "Booking Cancelled"
    BOOKING_RESCHEDULED = "booking.rescheduled", "Booking Rescheduled"
    BOOKING_COMPLETED = "booking.completed", "Booking Completed"
    BOOKING_NO_SHOW = "booking.no_show", "Booking No Show"
    
    # Payment events
    PAYMENT_RECEIVED = "payment.received", "Payment Received"
    PAYMENT_FAILED = "payment.failed", "Payment Failed"
    REFUND_PROCESSED = "payment.refund", "Refund Processed"
    
    # Service events
    SERVICE_PUBLISHED = "service.published", "Service Published"
    SERVICE_UPDATED = "service.updated", "Service Updated"
    
    # System events
    SYSTEM_ANNOUNCEMENT = "system.announcement", "System Announcement"
    SYSTEM_MAINTENANCE = "system.maintenance", "System Maintenance"
    
    # User events
    USER_WELCOME = "user.welcome", "Welcome"
    USER_PASSWORD_CHANGED = "user.password_changed", "Password Changed"


class NotificationChannel(models.TextChoices):
    """Delivery channels for notifications."""
    WEBSOCKET = "websocket", "WebSocket"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    PUSH = "push", "Push Notification"


class NotificationPriority(models.TextChoices):
    """Priority levels for notifications."""
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Notification(TimeStampedModel):
    """
    Persistent notification record.
    
    Stored for user access, read status tracking, and audit.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Recipient
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User this notification is for",
    )
    
    # Type and content
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title",
    )
    message = models.TextField(
        help_text="Notification message body",
    )
    
    # Data payload
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data payload",
    )
    
    # Links
    action_url = models.URLField(
        blank=True,
        help_text="URL for the notification action",
    )
    
    # Priority
    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    
    # Read status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    # Delivery tracking
    channels_sent = models.JSONField(
        default=list,
        blank=True,
        help_text="Channels through which notification was sent",
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification expires and should be hidden",
    )
    
    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "notification_type"]),
            models.Index(fields=["user", "created_at"]),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at", "updated_at"])
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationPreference(TimeStampedModel):
    """
    User preferences for notification delivery.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    
    # Channel preferences
    websocket_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    
    class Meta:
        db_table = "notification_preferences"
        unique_together = ["user", "notification_type"]
    
    def __str__(self):
        return f"{self.user.email}: {self.notification_type}"


class EventOutbox(TimeStampedModel):
    """
    Outbox pattern for reliable event delivery.
    
    Events are written here, then processed asynchronously.
    Ensures at-least-once delivery.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Event details
    event_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of event (e.g., order.created)",
    )
    aggregate_type = models.CharField(
        max_length=50,
        help_text="Type of entity (e.g., Order, Booking)",
    )
    aggregate_id = models.CharField(
        max_length=36,
        help_text="ID of the entity",
    )
    
    # Payload
    payload = models.JSONField(
        help_text="Event data payload",
    )
    
    # Processing status
    is_processed = models.BooleanField(
        default=False,
        db_index=True,
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    # Retry tracking
    retry_count = models.PositiveIntegerField(
        default=0,
    )
    max_retries = models.PositiveIntegerField(
        default=5,
    )
    last_error = models.TextField(
        blank=True,
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    class Meta:
        db_table = "event_outbox"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["is_processed", "created_at"]),
            models.Index(fields=["event_type", "is_processed"]),
            models.Index(fields=["aggregate_type", "aggregate_id"]),
        ]
    
    def __str__(self):
        return f"{self.event_type}: {self.aggregate_type}#{self.aggregate_id}"
    
    def mark_processed(self):
        """Mark event as processed."""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save(update_fields=["is_processed", "processed_at", "updated_at"])
    
    def record_error(self, error: str):
        """Record processing error."""
        self.retry_count += 1
        self.last_error = error
        
        # Exponential backoff: 1min, 2min, 4min, 8min, 16min
        backoff_minutes = 2 ** self.retry_count
        self.next_retry_at = timezone.now() + timezone.timedelta(minutes=backoff_minutes)
        
        self.save(update_fields=[
            "retry_count",
            "last_error",
            "next_retry_at",
            "updated_at",
        ])
    
    @property
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self.retry_count < self.max_retries
