"""
Booking Admin Configuration.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AvailabilitySchedule,
    AvailabilitySlot,
    BlockedTime,
    Booking,
    BookingStatusHistory,
)


class AvailabilitySlotInline(admin.TabularInline):
    model = AvailabilitySlot
    extra = 1
    fields = ["day_of_week", "start_time", "end_time"]


@admin.register(AvailabilitySchedule)
class AvailabilityScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "provider",
        "service",
        "effective_from",
        "effective_until",
        "is_active",
        "slot_count",
    ]
    list_filter = ["is_active", "service"]
    search_fields = [
        "name",
        "provider__user__email",
        "provider__user__first_name",
        "service__name",
    ]
    inlines = [AvailabilitySlotInline]
    raw_id_fields = ["provider", "service"]
    
    def slot_count(self, obj):
        return obj.slots.count()
    slot_count.short_description = "Slots"


@admin.register(BlockedTime)
class BlockedTimeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "provider",
        "service",
        "start_datetime",
        "end_datetime",
        "is_all_day",
        "is_recurring",
    ]
    list_filter = ["is_all_day", "is_recurring", "service"]
    search_fields = [
        "title",
        "provider__user__email",
        "service__name",
    ]
    date_hierarchy = "start_datetime"
    raw_id_fields = ["provider", "service"]


class BookingStatusHistoryInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "notes", "created_at"]
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "service",
        "provider_name",
        "customer_name",
        "start_datetime",
        "status_badge",
        "attendee_count",
        "total_price",
        "created_at",
    ]
    list_filter = [
        "status",
        "service",
        "start_datetime",
        "created_at",
    ]
    search_fields = [
        "reference",
        "service__name",
        "provider__user__email",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
    ]
    date_hierarchy = "start_datetime"
    readonly_fields = [
        "reference",
        "created_at",
        "updated_at",
        "confirmed_at",
        "cancelled_at",
        "completed_at",
    ]
    raw_id_fields = [
        "service",
        "provider",
        "customer",
        "confirmed_by",
        "cancelled_by",
        "order",
        "rescheduled_from",
    ]
    inlines = [BookingStatusHistoryInline]
    
    fieldsets = (
        (None, {
            "fields": ("reference", "service", "provider", "customer"),
        }),
        ("Schedule", {
            "fields": ("start_datetime", "end_datetime", "status"),
        }),
        ("Attendees", {
            "fields": ("attendee_count", "attendee_names"),
        }),
        ("Pricing", {
            "fields": ("unit_price", "total_price", "currency", "addons"),
        }),
        ("Notes", {
            "fields": ("customer_notes", "internal_notes"),
        }),
        ("Confirmation", {
            "fields": ("confirmed_at", "confirmed_by"),
            "classes": ("collapse",),
        }),
        ("Cancellation", {
            "fields": (
                "cancelled_at",
                "cancelled_by",
                "cancellation_reason",
                "cancellation_notes",
            ),
            "classes": ("collapse",),
        }),
        ("Completion & Links", {
            "fields": ("completed_at", "order", "rescheduled_from", "reminder_sent_at"),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    def provider_name(self, obj):
        if obj.provider:
            return obj.provider.user.get_full_name()
        return "-"
    provider_name.short_description = "Provider"
    
    def customer_name(self, obj):
        return obj.customer.get_full_name()
    customer_name.short_description = "Customer"
    
    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "confirmed": "#28a745",
            "in_progress": "#17a2b8",
            "completed": "#6c757d",
            "cancelled": "#dc3545",
            "no_show": "#dc3545",
            "rescheduled": "#6610f2",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"
