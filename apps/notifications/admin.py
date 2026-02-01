"""
Notification Admin Configuration.
"""

from django.contrib import admin

from .models import EventOutbox, Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "user",
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    ]
    list_filter = [
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    ]
    search_fields = [
        "title",
        "message",
        "user__email",
    ]
    readonly_fields = ["created_at", "updated_at", "read_at"]
    date_hierarchy = "created_at"
    raw_id_fields = ["user"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "notification_type",
        "websocket_enabled",
        "email_enabled",
        "sms_enabled",
        "push_enabled",
    ]
    list_filter = [
        "notification_type",
        "websocket_enabled",
        "email_enabled",
    ]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]


@admin.register(EventOutbox)
class EventOutboxAdmin(admin.ModelAdmin):
    list_display = [
        "event_type",
        "aggregate_type",
        "aggregate_id",
        "is_processed",
        "retry_count",
        "created_at",
    ]
    list_filter = [
        "event_type",
        "aggregate_type",
        "is_processed",
        "created_at",
    ]
    search_fields = ["aggregate_id", "event_type"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "processed_at",
    ]
    date_hierarchy = "created_at"
