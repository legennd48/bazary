"""
Notification Services.

Business logic for notification dispatch and event handling.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .models import (
    EventOutbox,
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationPriority,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for creating and dispatching notifications.
    """
    
    @staticmethod
    def create_notification(
        user,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        action_url: str = "",
        priority: str = NotificationPriority.NORMAL,
        channels: Optional[List[str]] = None,
        expires_at=None,
    ) -> Notification:
        """
        Create and dispatch a notification.
        
        Args:
            user: User to notify
            notification_type: Type from NotificationType
            title: Notification title
            message: Message body
            data: Additional data payload
            action_url: URL for action button
            priority: Priority level
            channels: Delivery channels (defaults to user preferences)
            expires_at: When notification expires
        
        Returns:
            Created Notification instance
        """
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            priority=priority,
            expires_at=expires_at,
        )
        
        # Determine channels
        if channels is None:
            channels = NotificationService._get_user_channels(
                user,
                notification_type,
            )
        
        # Dispatch to channels
        channels_sent = []
        
        if NotificationChannel.WEBSOCKET in channels:
            try:
                NotificationService._send_websocket(notification)
                channels_sent.append(NotificationChannel.WEBSOCKET)
            except Exception as e:
                logger.error(f"WebSocket send failed: {e}")
        
        if NotificationChannel.EMAIL in channels:
            try:
                NotificationService._send_email(notification)
                channels_sent.append(NotificationChannel.EMAIL)
            except Exception as e:
                logger.error(f"Email send failed: {e}")
        
        # Update channels_sent
        notification.channels_sent = channels_sent
        notification.save(update_fields=["channels_sent"])
        
        return notification
    
    @staticmethod
    def _get_user_channels(user, notification_type: str) -> List[str]:
        """Get enabled channels for user and notification type."""
        channels = []
        
        # Check preferences
        try:
            pref = NotificationPreference.objects.get(
                user=user,
                notification_type=notification_type,
            )
            
            if pref.websocket_enabled:
                channels.append(NotificationChannel.WEBSOCKET)
            if pref.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if pref.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if pref.push_enabled:
                channels.append(NotificationChannel.PUSH)
        
        except NotificationPreference.DoesNotExist:
            # Default: WebSocket + Email for most types
            channels = [
                NotificationChannel.WEBSOCKET,
                NotificationChannel.EMAIL,
            ]
        
        return channels
    
    @staticmethod
    def _send_websocket(notification: Notification):
        """Send notification via WebSocket."""
        channel_layer = get_channel_layer()
        
        if not channel_layer:
            logger.warning("Channel layer not configured")
            return
        
        # User-specific channel group
        group_name = f"user_{notification.user.id}"
        
        message = {
            "type": "notification.message",
            "notification": {
                "id": str(notification.id),
                "type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data,
                "action_url": notification.action_url,
                "priority": notification.priority,
                "created_at": notification.created_at.isoformat(),
            },
        }
        
        async_to_sync(channel_layer.group_send)(group_name, message)
    
    @staticmethod
    def _send_email(notification: Notification):
        """Queue email notification via Celery."""
        from apps.core.tasks import send_notification_email
        
        send_notification_email.delay(
            user_id=str(notification.user.id),
            notification_id=str(notification.id),
        )
    
    @staticmethod
    def mark_read(notification_ids: List[str], user):
        """Mark notifications as read."""
        Notification.objects.filter(
            id__in=notification_ids,
            user=user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
    
    @staticmethod
    def mark_all_read(user):
        """Mark all user notifications as read."""
        from django.utils import timezone
        
        Notification.objects.filter(
            user=user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
    
    @staticmethod
    def get_unread_count(user) -> int:
        """Get count of unread notifications."""
        return Notification.objects.filter(
            user=user,
            is_read=False,
        ).count()


class EventService:
    """
    Service for event outbox pattern.
    
    Ensures reliable event delivery with at-least-once semantics.
    """
    
    @staticmethod
    @transaction.atomic
    def publish_event(
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
    ) -> EventOutbox:
        """
        Publish an event to the outbox.
        
        The event will be processed asynchronously by a worker.
        
        Args:
            event_type: Type of event (e.g., "order.created")
            aggregate_type: Type of entity (e.g., "Order")
            aggregate_id: ID of the entity
            payload: Event data
        
        Returns:
            Created EventOutbox instance
        """
        event = EventOutbox.objects.create(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
        )
        
        # Trigger async processing
        from apps.notifications.tasks import process_outbox_event
        process_outbox_event.delay(str(event.id))
        
        return event
    
    @staticmethod
    def process_pending_events(batch_size: int = 100):
        """
        Process pending events in the outbox.
        
        Called by a scheduled task to catch any events that weren't
        processed immediately.
        """
        from django.utils import timezone
        
        events = EventOutbox.objects.filter(
            is_processed=False,
            retry_count__lt=models.F("max_retries"),
        ).filter(
            models.Q(next_retry_at__isnull=True)
            | models.Q(next_retry_at__lte=timezone.now())
        ).order_by("created_at")[:batch_size]
        
        for event in events:
            try:
                EventService._handle_event(event)
                event.mark_processed()
            except Exception as e:
                logger.error(f"Event processing failed: {event.id} - {e}")
                event.record_error(str(e))
    
    @staticmethod
    def _handle_event(event: EventOutbox):
        """Handle a single event."""
        handlers = EventService._get_handlers(event.event_type)
        
        for handler in handlers:
            handler(event)
    
    @staticmethod
    def _get_handlers(event_type: str) -> List[callable]:
        """Get handlers for an event type."""
        from apps.notifications.handlers import EVENT_HANDLERS
        
        handlers = EVENT_HANDLERS.get(event_type, [])
        
        # Also check wildcard handlers
        parts = event_type.split(".")
        if len(parts) == 2:
            wildcard = f"{parts[0]}.*"
            handlers.extend(EVENT_HANDLERS.get(wildcard, []))
        
        return handlers
