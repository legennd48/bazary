"""
Service Admin Configuration.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Service,
    ServiceAddon,
    ServiceCategory,
    ServiceImage,
    ServiceProvider,
)


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ["image", "alt_text", "sort_order"]


class ServiceAddonInline(admin.TabularInline):
    model = ServiceAddon
    extra = 0
    fields = ["name", "price", "duration_minutes", "is_active"]


class ServiceProviderInline(admin.TabularInline):
    model = ServiceProvider
    extra = 0
    fields = ["user", "is_primary", "is_active", "custom_price", "custom_duration"]
    raw_id_fields = ["user"]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "parent",
        "is_active",
        "service_count",
        "sort_order",
    ]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["sort_order", "name"]
    
    def service_count(self, obj):
        return obj.services.count()
    service_count.short_description = "Services"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category",
        "status_badge",
        "pricing_display",
        "duration_minutes",
        "provider_count",
        "created_at",
    ]
    list_filter = [
        "status",
        "pricing_type",
        "category",
        "requires_booking",
        "created_at",
    ]
    search_fields = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at", "created_by"]
    raw_id_fields = ["category"]
    inlines = [ServiceImageInline, ServiceAddonInline, ServiceProviderInline]
    
    fieldsets = (
        (None, {
            "fields": ("name", "slug", "short_description", "description"),
        }),
        ("Categorization", {
            "fields": ("category", "tags", "status"),
        }),
        ("Pricing", {
            "fields": (
                "pricing_type",
                "price",
                "compare_price",
                "currency",
            ),
        }),
        ("Duration & Capacity", {
            "fields": (
                "duration_minutes",
                "buffer_before_minutes",
                "buffer_after_minutes",
                "max_attendees",
                "min_attendees",
            ),
        }),
        ("Booking Settings", {
            "fields": (
                "requires_booking",
                "advance_booking_days",
                "min_notice_hours",
                "cancellation_policy",
                "free_cancellation_hours",
            ),
        }),
        ("Media", {
            "fields": ("featured_image",),
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description"),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            "draft": "#6c757d",
            "active": "#28a745",
            "inactive": "#ffc107",
            "archived": "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"
    
    def pricing_display(self, obj):
        if obj.pricing_type == "free":
            return "Free"
        return f"{obj.currency} {obj.price} / {obj.get_pricing_type_display()}"
    pricing_display.short_description = "Pricing"
    
    def provider_count(self, obj):
        return obj.providers.filter(is_active=True).count()
    provider_count.short_description = "Providers"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "service",
        "is_primary",
        "is_active",
        "custom_price",
        "custom_duration",
    ]
    list_filter = ["is_primary", "is_active", "service__category"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "service__name",
    ]
    raw_id_fields = ["user", "service"]


@admin.register(ServiceAddon)
class ServiceAddonAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "service",
        "price",
        "duration_minutes",
        "is_active",
    ]
    list_filter = ["is_active", "service"]
    search_fields = ["name", "service__name"]
    raw_id_fields = ["service"]
