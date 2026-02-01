"""
Notification Celery Tasks.

Async tasks for notification processing and delivery.
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name="notifications.process_outbox_event",
    bind=True,
    max_retries=5,
    default_retry_delay=60,
)
def process_outbox_event(self, event_id: str):
    """
    Process a single event from the outbox.
    
    Args:
        event_id: UUID of the EventOutbox record
    """
    from apps.notifications.models import EventOutbox
    from apps.notifications.services import EventService
    
    try:
        event = EventOutbox.objects.get(id=event_id, is_processed=False)
    except EventOutbox.DoesNotExist:
        logger.warning(f"Event not found or already processed: {event_id}")
        return
    
    try:
        EventService._handle_event(event)
        event.mark_processed()
        logger.info(f"Event processed: {event.event_type} - {event_id}")
    
    except Exception as e:
        logger.error(f"Event processing failed: {event_id} - {e}")
        event.record_error(str(e))
        
        if event.can_retry:
            raise self.retry(exc=e)


@shared_task(name="notifications.process_pending_events")
def process_pending_events():
    """
    Process any pending events in the outbox.
    
    Scheduled task to catch events that weren't processed immediately.
    Should run every minute.
    """
    from apps.notifications.models import EventOutbox
    from django.db import models
    
    events = EventOutbox.objects.filter(
        is_processed=False,
        retry_count__lt=models.F("max_retries"),
    ).filter(
        models.Q(next_retry_at__isnull=True)
        | models.Q(next_retry_at__lte=timezone.now())
    ).order_by("created_at")[:100]
    
    for event in events:
        process_outbox_event.delay(str(event.id))
    
    return f"Queued {len(events)} events for processing"


@shared_task(name="notifications.send_notification_email")
def send_notification_email(user_id: str, notification_id: str):
    """
    Send notification email.
    
    Args:
        user_id: User UUID
        notification_id: Notification UUID
    """
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.conf import settings
    from apps.notifications.models import Notification
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        notification = Notification.objects.get(id=notification_id)
    except (User.DoesNotExist, Notification.DoesNotExist):
        logger.warning(f"User or notification not found: {user_id}, {notification_id}")
        return
    
    # Skip if already sent via email
    if "email" in notification.channels_sent:
        return
    
    try:
        send_mail(
            subject=notification.title,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        # Update channels_sent
        notification.channels_sent = list(notification.channels_sent) + ["email"]
        notification.save(update_fields=["channels_sent"])
        
        logger.info(f"Email sent for notification: {notification_id}")
    
    except Exception as e:
        logger.error(f"Email send failed: {notification_id} - {e}")
        raise


@shared_task(name="notifications.send_booking_reminders")
def send_booking_reminders():
    """
    Send booking reminders for tomorrow's bookings.
    
    Should run daily, typically in the evening.
    """
    from datetime import timedelta
    from apps.bookings.models import Booking, BookingStatus
    from apps.notifications.services import EventService
    
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    bookings = Booking.objects.filter(
        status=BookingStatus.CONFIRMED,
        start_datetime__date=tomorrow,
        reminder_sent_at__isnull=True,
    ).select_related("service", "customer")
    
    for booking in bookings:
        # Publish reminder event
        EventService.publish_event(
            event_type="booking.reminder",
            aggregate_type="Booking",
            aggregate_id=str(booking.id),
            payload={
                "customer_id": str(booking.customer.id),
                "reference": booking.reference,
                "service_name": booking.service.name,
                "date": booking.start_datetime.strftime("%Y-%m-%d"),
                "time": booking.start_datetime.strftime("%H:%M"),
            },
        )
        
        # Mark reminder sent
        booking.reminder_sent_at = timezone.now()
        booking.save(update_fields=["reminder_sent_at"])
    
    return f"Sent {len(bookings)} booking reminders"


@shared_task(name="notifications.cleanup_old_notifications")
def cleanup_old_notifications(days: int = 90):
    """
    Clean up old read notifications.
    
    Args:
        days: Delete read notifications older than this many days
    """
    from datetime import timedelta
    from apps.notifications.models import Notification
    
    cutoff = timezone.now() - timedelta(days=days)
    
    deleted, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff,
    ).delete()
    
    return f"Deleted {deleted} old notifications"


@shared_task(name="notifications.cleanup_processed_events")
def cleanup_processed_events(days: int = 30):
    """
    Clean up processed events from outbox.
    
    Args:
        days: Delete processed events older than this many days
    """
    from datetime import timedelta
    from apps.notifications.models import EventOutbox
    
    cutoff = timezone.now() - timedelta(days=days)
    
    deleted, _ = EventOutbox.objects.filter(
        is_processed=True,
        processed_at__lt=cutoff,
    ).delete()
    
    return f"Deleted {deleted} processed events"
