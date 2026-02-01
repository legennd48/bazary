"""
Notification Views.

REST API for notification management.
"""

from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.capabilities.registry import require_capability

from .models import Notification, NotificationPreference, NotificationType
from .serializers import (
    MarkReadSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
    NotificationSerializer,
)


class NotificationFilter(filters.FilterSet):
    """Filters for notifications."""
    
    type = filters.ChoiceFilter(
        field_name="notification_type",
        choices=NotificationType.choices,
    )
    is_read = filters.BooleanFilter()
    priority = filters.CharFilter()
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    
    class Meta:
        model = Notification
        fields = ["type", "is_read", "priority"]


@require_capability("notifications")
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Notification management.
    
    Endpoints:
    - GET /notifications/ - List user notifications
    - GET /notifications/{id}/ - Get notification details
    - POST /notifications/mark-read/ - Mark notifications as read
    - POST /notifications/mark-all-read/ - Mark all as read
    - GET /notifications/unread-count/ - Get unread count
    """
    
    queryset = Notification.objects.all()
    filterset_class = NotificationFilter
    permission_classes = [IsAuthenticated]
    lookup_field = "id"
    
    def get_serializer_class(self):
        if self.action == "list":
            return NotificationListSerializer
        if self.action == "mark_read":
            return MarkReadSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Users only see their own notifications
        qs = qs.filter(user=self.request.user)
        
        # Exclude expired
        qs = qs.filter(
            models.Q(expires_at__isnull=True)
            | models.Q(expires_at__gt=timezone.now())
        )
        
        return qs.order_by("-created_at")
    
    @action(detail=False, methods=["post"], url_path="mark-read")
    def mark_read(self, request):
        """Mark specific notifications as read."""
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data["notification_ids"]
        
        updated = Notification.objects.filter(
            id__in=notification_ids,
            user=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
        
        return Response({
            "message": f"Marked {updated} notifications as read",
            "count": updated,
        })
    
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )
        
        return Response({
            "message": f"Marked {updated} notifications as read",
            "count": updated,
        })
    
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Get unread notification count."""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).filter(
            models.Q(expires_at__isnull=True)
            | models.Q(expires_at__gt=timezone.now())
        ).count()
        
        return Response({"unread_count": count})


@require_capability("notifications")
class NotificationPreferenceView(APIView):
    """
    Manage notification preferences.
    
    Endpoints:
    - GET /notifications/preferences/ - Get all preferences
    - PUT /notifications/preferences/ - Update preferences
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's notification preferences."""
        # Get existing preferences
        existing = {
            p.notification_type: p
            for p in NotificationPreference.objects.filter(user=request.user)
        }
        
        # Build response with defaults for missing types
        preferences = []
        
        for choice in NotificationType.choices:
            type_value = choice[0]
            type_display = choice[1]
            
            if type_value in existing:
                pref = existing[type_value]
                preferences.append({
                    "notification_type": type_value,
                    "type_display": type_display,
                    "websocket_enabled": pref.websocket_enabled,
                    "email_enabled": pref.email_enabled,
                    "sms_enabled": pref.sms_enabled,
                    "push_enabled": pref.push_enabled,
                })
            else:
                # Default preferences
                preferences.append({
                    "notification_type": type_value,
                    "type_display": type_display,
                    "websocket_enabled": True,
                    "email_enabled": True,
                    "sms_enabled": False,
                    "push_enabled": True,
                })
        
        return Response({"preferences": preferences})
    
    def put(self, request):
        """Update notification preferences."""
        serializer = NotificationPreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        notification_type = data["notification_type"]
        
        # Get or create preference
        pref, created = NotificationPreference.objects.get_or_create(
            user=request.user,
            notification_type=notification_type,
            defaults={
                "websocket_enabled": data.get("websocket_enabled", True),
                "email_enabled": data.get("email_enabled", True),
                "sms_enabled": data.get("sms_enabled", False),
                "push_enabled": data.get("push_enabled", True),
            },
        )
        
        if not created:
            # Update existing
            if "websocket_enabled" in data:
                pref.websocket_enabled = data["websocket_enabled"]
            if "email_enabled" in data:
                pref.email_enabled = data["email_enabled"]
            if "sms_enabled" in data:
                pref.sms_enabled = data["sms_enabled"]
            if "push_enabled" in data:
                pref.push_enabled = data["push_enabled"]
            pref.save()
        
        return Response(NotificationPreferenceSerializer(pref).data)


# Import models for Q expressions
from django.db import models
