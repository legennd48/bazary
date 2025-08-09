"""
Payment admin configuration.

This module configures the Django admin interface for payment-related models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Cart, CartItem, PaymentMethod, PaymentProvider, Transaction


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentProvider model."""

    list_display = [
        "name",
        "provider_type",
        "is_active",
        "test_mode",
        "supported_currencies_display",
        "created_at",
    ]
    list_filter = ["provider_type", "is_active", "test_mode", "created_at"]
    search_fields = ["name", "provider_type"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "provider_type", "is_active")}),
        (
            "Configuration",
            {"fields": ("api_key", "secret_key", "webhook_secret", "test_mode")},
        ),
        ("Features", {"fields": ("supported_currencies", "configuration")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def supported_currencies_display(self, obj):
        """Display supported currencies as comma-separated list."""
        return (
            ", ".join(obj.supported_currencies) if obj.supported_currencies else "None"
        )

    supported_currencies_display.short_description = "Supported Currencies"


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin configuration for PaymentMethod model."""

    list_display = [
        "name",
        "user",
        "provider",
        "method_type",
        "is_default",
        "is_active",
        "last_four_display",
        "expires_at",
        "created_at",
    ]
    list_filter = [
        "method_type",
        "is_default",
        "is_active",
        "provider__provider_type",
        "expires_at",
        "created_at",
    ]
    search_fields = ["name", "user__email", "provider__name", "last_four"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["user", "provider"]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "provider", "method_type", "name")}),
        ("Status", {"fields": ("is_default", "is_active")}),
        ("Provider Details", {"fields": ("provider_method_id", "metadata")}),
        (
            "Card Information",
            {
                "fields": ("last_four", "card_brand", "expires_at"),
                "description": "Only applicable for card payment methods",
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def last_four_display(self, obj):
        """Display last four digits with masking."""
        if obj.last_four:
            return f"****{obj.last_four}"
        return "N/A"

    last_four_display.short_description = "Card Number"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model."""

    list_display = [
        "id",
        "user",
        "transaction_type",
        "status_display",
        "amount",
        "currency",
        "provider",
        "created_at",
    ]
    list_filter = [
        "transaction_type",
        "status",
        "currency",
        "provider__name",
        "created_at",
        "processed_at",
    ]
    search_fields = [
        "id",
        "user__email",
        "provider_transaction_id",
        "reference",
        "description",
    ]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "processed_at",
        "failed_at",
    ]
    raw_id_fields = ["user", "payment_method", "provider", "parent_transaction"]

    fieldsets = (
        (
            "Transaction Details",
            {
                "fields": (
                    "id",
                    "user",
                    "payment_method",
                    "provider",
                    "transaction_type",
                    "status",
                )
            },
        ),
        ("Amount Information", {"fields": ("amount", "currency", "provider_fee")}),
        (
            "Provider Details",
            {
                "fields": (
                    "provider_transaction_id",
                    "description",
                    "reference",
                    "metadata",
                )
            },
        ),
        (
            "Status & Timing",
            {
                "fields": (
                    "processed_at",
                    "failed_at",
                    "error_message",
                )
            },
        ),
        (
            "Related Transactions",
            {
                "fields": ("parent_transaction",),
                "description": "For refunds and chargebacks",
            },
        ),
        ("Raw Data", {"fields": ("webhook_data",), "classes": ("collapse",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            "pending": "orange",
            "processing": "blue",
            "succeeded": "green",
            "failed": "red",
            "cancelled": "gray",
            "refunded": "purple",
            "partially_refunded": "purple",
        }
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {};">{}</span>', color, obj.get_status_display()
        )

    status_display.short_description = "Status"

    def has_change_permission(self, request, obj=None):
        """Limit transaction editing to specific fields."""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Make most fields readonly for existing transactions."""
        if obj:  # Editing existing transaction
            return [
                "id",
                "user",
                "payment_method",
                "provider",
                "transaction_type",
                "amount",
                "currency",
                "provider_transaction_id",
                "provider_fee",
                "processed_at",
                "failed_at",
                "parent_transaction",
                "webhook_data",
                "created_at",
                "updated_at",
            ]
        return self.readonly_fields


class CartItemInline(admin.TabularInline):
    """Inline admin for cart items."""

    model = CartItem
    extra = 0
    readonly_fields = ["line_total", "created_at", "updated_at"]
    raw_id_fields = ["product", "variant"]

    fields = [
        "product",
        "variant",
        "quantity",
        "unit_price",
        "line_total",
        "notes",
    ]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin configuration for Cart model."""

    list_display = [
        "id",
        "user",
        "status",
        "item_count_display",
        "total",
        "currency",
        "created_at",
    ]
    list_filter = ["status", "currency", "created_at", "expires_at"]
    search_fields = ["id", "user__email", "session_key", "notes"]
    readonly_fields = [
        "id",
        "subtotal",
        "tax_amount",
        "shipping_amount",
        "total",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["user"]
    inlines = [CartItemInline]

    fieldsets = (
        (
            "Cart Information",
            {"fields": ("id", "user", "session_key", "status", "currency")},
        ),
        (
            "Pricing",
            {
                "fields": (
                    "subtotal",
                    "tax_amount",
                    "shipping_amount",
                    "discount_amount",
                    "total",
                )
            },
        ),
        ("Additional Information", {"fields": ("notes", "metadata", "expires_at")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def item_count_display(self, obj):
        """Display total item count."""
        return obj.item_count

    item_count_display.short_description = "Items"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin configuration for CartItem model."""

    list_display = [
        "id",
        "cart",
        "product",
        "variant",
        "quantity",
        "unit_price",
        "line_total",
        "created_at",
    ]
    list_filter = ["created_at", "updated_at"]
    search_fields = [
        "cart__id",
        "cart__user__email",
        "product__name",
        "variant__sku",
        "notes",
    ]
    readonly_fields = ["line_total", "created_at", "updated_at"]
    raw_id_fields = ["cart", "product", "variant"]

    fieldsets = (
        (
            "Item Information",
            {"fields": ("cart", "product", "variant", "quantity", "unit_price")},
        ),
        ("Pricing", {"fields": ("line_total",)}),
        ("Additional Information", {"fields": ("custom_attributes", "notes")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
