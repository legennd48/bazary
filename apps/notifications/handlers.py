"""
Event Handlers.

Maps event types to handler functions for notification dispatch.
"""

import logging
from typing import Dict, List

from .models import EventOutbox, NotificationPriority, NotificationType

logger = logging.getLogger(__name__)


def handle_order_created(event: EventOutbox):
    """Handle order.created event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        logger.warning(f"User not found for order event: {event.id}")
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.ORDER_CREATED,
        title="Order Received",
        message=f"Your order #{payload.get('order_number')} has been received and is being processed.",
        data={
            "order_id": event.aggregate_id,
            "order_number": payload.get("order_number"),
        },
        action_url=f"/orders/{event.aggregate_id}",
        priority=NotificationPriority.NORMAL,
    )


def handle_order_confirmed(event: EventOutbox):
    """Handle order.confirmed event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.ORDER_CONFIRMED,
        title="Order Confirmed",
        message=f"Your order #{payload.get('order_number')} has been confirmed.",
        data={
            "order_id": event.aggregate_id,
            "order_number": payload.get("order_number"),
        },
        action_url=f"/orders/{event.aggregate_id}",
        priority=NotificationPriority.NORMAL,
    )


def handle_order_paid(event: EventOutbox):
    """Handle order.paid event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.ORDER_PAID,
        title="Payment Received",
        message=f"Payment for order #{payload.get('order_number')} has been received. Thank you!",
        data={
            "order_id": event.aggregate_id,
            "order_number": payload.get("order_number"),
            "amount": str(payload.get("amount", "")),
        },
        action_url=f"/orders/{event.aggregate_id}",
        priority=NotificationPriority.NORMAL,
    )


def handle_order_shipped(event: EventOutbox):
    """Handle order.shipped event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.ORDER_SHIPPED,
        title="Order Shipped!",
        message=f"Your order #{payload.get('order_number')} is on its way!",
        data={
            "order_id": event.aggregate_id,
            "order_number": payload.get("order_number"),
            "tracking_number": payload.get("tracking_number"),
            "carrier": payload.get("carrier"),
        },
        action_url=f"/orders/{event.aggregate_id}",
        priority=NotificationPriority.HIGH,
    )


def handle_order_cancelled(event: EventOutbox):
    """Handle order.cancelled event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.ORDER_CANCELLED,
        title="Order Cancelled",
        message=f"Your order #{payload.get('order_number')} has been cancelled.",
        data={
            "order_id": event.aggregate_id,
            "order_number": payload.get("order_number"),
            "reason": payload.get("reason", ""),
        },
        action_url=f"/orders/{event.aggregate_id}",
        priority=NotificationPriority.HIGH,
    )


def handle_booking_created(event: EventOutbox):
    """Handle booking.created event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.BOOKING_CREATED,
        title="Booking Received",
        message=f"Your booking for {payload.get('service_name')} on {payload.get('date')} has been received.",
        data={
            "booking_id": event.aggregate_id,
            "booking_reference": payload.get("reference"),
            "service_name": payload.get("service_name"),
            "date": payload.get("date"),
            "time": payload.get("time"),
        },
        action_url=f"/bookings/{event.aggregate_id}",
        priority=NotificationPriority.NORMAL,
    )


def handle_booking_confirmed(event: EventOutbox):
    """Handle booking.confirmed event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.BOOKING_CONFIRMED,
        title="Booking Confirmed!",
        message=f"Your booking for {payload.get('service_name')} on {payload.get('date')} at {payload.get('time')} is confirmed!",
        data={
            "booking_id": event.aggregate_id,
            "booking_reference": payload.get("reference"),
            "service_name": payload.get("service_name"),
            "date": payload.get("date"),
            "time": payload.get("time"),
            "provider_name": payload.get("provider_name"),
        },
        action_url=f"/bookings/{event.aggregate_id}",
        priority=NotificationPriority.HIGH,
    )


def handle_booking_cancelled(event: EventOutbox):
    """Handle booking.cancelled event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.BOOKING_CANCELLED,
        title="Booking Cancelled",
        message=f"Your booking for {payload.get('service_name')} has been cancelled.",
        data={
            "booking_id": event.aggregate_id,
            "booking_reference": payload.get("reference"),
            "service_name": payload.get("service_name"),
            "reason": payload.get("reason", ""),
        },
        action_url=f"/bookings/{event.aggregate_id}",
        priority=NotificationPriority.HIGH,
    )


def handle_booking_reminder(event: EventOutbox):
    """Handle booking.reminder event."""
    from django.contrib.auth import get_user_model
    from .services import NotificationService
    
    User = get_user_model()
    payload = event.payload
    
    try:
        user = User.objects.get(id=payload.get("customer_id"))
    except User.DoesNotExist:
        return
    
    NotificationService.create_notification(
        user=user,
        notification_type=NotificationType.BOOKING_REMINDER,
        title="Booking Reminder",
        message=f"Reminder: Your {payload.get('service_name')} booking is tomorrow at {payload.get('time')}!",
        data={
            "booking_id": event.aggregate_id,
            "booking_reference": payload.get("reference"),
            "service_name": payload.get("service_name"),
            "date": payload.get("date"),
            "time": payload.get("time"),
        },
        action_url=f"/bookings/{event.aggregate_id}",
        priority=NotificationPriority.HIGH,
    )


# Event handler registry
EVENT_HANDLERS: Dict[str, List[callable]] = {
    # Order events
    "order.created": [handle_order_created],
    "order.confirmed": [handle_order_confirmed],
    "order.paid": [handle_order_paid],
    "order.shipped": [handle_order_shipped],
    "order.cancelled": [handle_order_cancelled],
    
    # Booking events
    "booking.created": [handle_booking_created],
    "booking.confirmed": [handle_booking_confirmed],
    "booking.cancelled": [handle_booking_cancelled],
    "booking.reminder": [handle_booking_reminder],
}
