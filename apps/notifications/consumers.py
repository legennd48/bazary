"""
WebSocket Consumers for Real-Time Notifications.

JWT-authenticated WebSocket connections for notification delivery.
"""

import json
import logging
from typing import Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    
    Supports JWT authentication via:
    1. Query parameter: ?token=<jwt>
    2. First message: {"type": "auth", "token": "<jwt>"}
    
    Messages sent to client:
    - notification.message: New notification
    - notification.count: Unread count update
    - connection.established: Successful connection
    - error: Error message
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_group = None
        self.authenticated = False
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        
        # Try to authenticate from query string
        token = self._get_token_from_query()
        
        if token:
            user = await self._authenticate_token(token)
            if user:
                await self._setup_authenticated_connection(user)
                return
        
        # Wait for auth message
        await self.send_json({
            "type": "auth.required",
            "message": "Please authenticate with a JWT token",
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.user_group:
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name,
            )
        
        logger.debug(f"WebSocket disconnected: {self.user_group} ({close_code})")
    
    async def receive_json(self, content):
        """Handle incoming WebSocket messages."""
        message_type = content.get("type")
        
        # Handle authentication
        if message_type == "auth":
            token = content.get("token")
            if token:
                user = await self._authenticate_token(token)
                if user:
                    await self._setup_authenticated_connection(user)
                else:
                    await self.send_json({
                        "type": "error",
                        "message": "Invalid or expired token",
                    })
                    await self.close(code=4001)
            return
        
        # Require authentication for other messages
        if not self.authenticated:
            await self.send_json({
                "type": "error",
                "message": "Not authenticated",
            })
            return
        
        # Handle other message types
        if message_type == "mark_read":
            notification_ids = content.get("notification_ids", [])
            await self._mark_notifications_read(notification_ids)
        
        elif message_type == "mark_all_read":
            await self._mark_all_notifications_read()
        
        elif message_type == "get_unread_count":
            count = await self._get_unread_count()
            await self.send_json({
                "type": "notification.count",
                "count": count,
            })
        
        elif message_type == "ping":
            await self.send_json({"type": "pong"})
    
    async def notification_message(self, event):
        """Handle notification message from channel layer."""
        await self.send_json(event)
    
    async def notification_count(self, event):
        """Handle unread count update from channel layer."""
        await self.send_json(event)
    
    def _get_token_from_query(self) -> Optional[str]:
        """Extract token from query string."""
        query_string = self.scope.get("query_string", b"").decode()
        
        if not query_string:
            return None
        
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param[6:]
        
        return None
    
    @database_sync_to_async
    def _authenticate_token(self, token: str):
        """Validate JWT token and return user."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Validate token
            access_token = AccessToken(token)
            user_id = access_token.get("user_id")
            
            if not user_id:
                return None
            
            # Get user
            try:
                user = User.objects.get(id=user_id, is_active=True)
                return user
            except User.DoesNotExist:
                return None
        
        except Exception as e:
            logger.warning(f"Token authentication failed: {e}")
            return None
    
    async def _setup_authenticated_connection(self, user):
        """Set up authenticated connection."""
        self.user = user
        self.user_group = f"user_{user.id}"
        self.authenticated = True
        
        # Join user's notification group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name,
        )
        
        # Send connection established
        count = await self._get_unread_count()
        
        await self.send_json({
            "type": "connection.established",
            "user_id": str(user.id),
            "unread_count": count,
        })
        
        logger.debug(f"WebSocket authenticated: {self.user_group}")
    
    @database_sync_to_async
    def _get_unread_count(self) -> int:
        """Get unread notification count."""
        from .models import Notification
        
        if not self.user:
            return 0
        
        return Notification.objects.filter(
            user=self.user,
            is_read=False,
        ).count()
    
    @database_sync_to_async
    def _mark_notifications_read(self, notification_ids):
        """Mark specific notifications as read."""
        from django.utils import timezone
        from .models import Notification
        
        if not self.user or not notification_ids:
            return
        
        Notification.objects.filter(
            id__in=notification_ids,
            user=self.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
    
    @database_sync_to_async
    def _mark_all_notifications_read(self):
        """Mark all notifications as read."""
        from django.utils import timezone
        from .models import Notification
        
        if not self.user:
            return
        
        Notification.objects.filter(
            user=self.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )


class AdminNotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for admin/staff notifications.
    
    Receives system-wide events like new orders, bookings, etc.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.authenticated = False
    
    async def connect(self):
        """Handle WebSocket connection."""
        await self.accept()
        
        # Try to authenticate from query string
        token = self._get_token_from_query()
        
        if token:
            user = await self._authenticate_admin_token(token)
            if user:
                await self._setup_admin_connection(user)
                return
        
        await self.send_json({
            "type": "auth.required",
            "message": "Admin authentication required",
        })
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.authenticated:
            await self.channel_layer.group_discard(
                "admin_notifications",
                self.channel_name,
            )
    
    async def receive_json(self, content):
        """Handle incoming messages."""
        message_type = content.get("type")
        
        if message_type == "auth":
            token = content.get("token")
            if token:
                user = await self._authenticate_admin_token(token)
                if user:
                    await self._setup_admin_connection(user)
                else:
                    await self.send_json({
                        "type": "error",
                        "message": "Invalid token or not an admin",
                    })
                    await self.close(code=4001)
            return
        
        if not self.authenticated:
            await self.send_json({
                "type": "error",
                "message": "Not authenticated",
            })
    
    async def admin_notification(self, event):
        """Handle admin notification from channel layer."""
        await self.send_json(event)
    
    def _get_token_from_query(self) -> Optional[str]:
        """Extract token from query string."""
        query_string = self.scope.get("query_string", b"").decode()
        
        if not query_string:
            return None
        
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param[6:]
        
        return None
    
    @database_sync_to_async
    def _authenticate_admin_token(self, token: str):
        """Validate JWT token and check admin status."""
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            access_token = AccessToken(token)
            user_id = access_token.get("user_id")
            
            if not user_id:
                return None
            
            try:
                user = User.objects.get(id=user_id, is_active=True, is_staff=True)
                return user
            except User.DoesNotExist:
                return None
        
        except Exception as e:
            logger.warning(f"Admin token authentication failed: {e}")
            return None
    
    async def _setup_admin_connection(self, user):
        """Set up authenticated admin connection."""
        self.user = user
        self.authenticated = True
        
        # Join admin notification group
        await self.channel_layer.group_add(
            "admin_notifications",
            self.channel_name,
        )
        
        await self.send_json({
            "type": "connection.established",
            "user_id": str(user.id),
            "admin": True,
        })
