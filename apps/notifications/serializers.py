"""
Notification Serializers.
"""

from rest_framework import serializers

from .models import (
    Notification,
    NotificationPreference,
    NotificationPriority,
    NotificationType,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Full notification details."""
    
    is_expired = serializers.BooleanField(read_only=True)
    type_display = serializers.CharField(
        source="get_notification_type_display",
        read_only=True,
    )
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "type_display",
            "title",
            "message",
            "data",
            "action_url",
            "priority",
            "is_read",
            "read_at",
            "channels_sent",
            "expires_at",
            "is_expired",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "data",
            "action_url",
            "priority",
            "channels_sent",
            "expires_at",
            "created_at",
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """Minimal notification for lists."""
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "action_url",
            "priority",
            "is_read",
            "created_at",
        ]


class MarkReadSerializer(serializers.Serializer):
    """Mark notifications as read."""
    
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Notification preferences."""
    
    type_display = serializers.CharField(
        source="get_notification_type_display",
        read_only=True,
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "notification_type",
            "type_display",
            "websocket_enabled",
            "email_enabled",
            "sms_enabled",
            "push_enabled",
        ]
        read_only_fields = ["id", "notification_type"]


class NotificationPreferenceUpdateSerializer(serializers.Serializer):
    """Update notification preferences."""
    
    notification_type = serializers.ChoiceField(choices=NotificationType.choices)
    websocket_enabled = serializers.BooleanField(required=False)
    email_enabled = serializers.BooleanField(required=False)
    sms_enabled = serializers.BooleanField(required=False)
    push_enabled = serializers.BooleanField(required=False)
