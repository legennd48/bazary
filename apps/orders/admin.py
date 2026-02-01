"""Order admin configuration."""

from django.contrib import admin

from .models import Order, OrderItem, OrderNote, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ["id", "subtotal", "total", "created_at"]
    fields = [
        "name",
        "sku",
        "item_type",
        "unit_price",
        "quantity",
        "discount_amount",
        "subtotal",
        "fulfillment_status",
        "quantity_fulfilled",
    ]


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline for order status history."""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "changed_by", "reason", "created_at"]
    can_delete = False


class OrderNoteInline(admin.TabularInline):
    """Inline for order notes."""
    model = OrderNote
    extra = 0
    fields = ["content", "author", "is_customer_visible", "created_at"]
    readonly_fields = ["author", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for orders."""
    
    list_display = [
        "order_number",
        "customer_email",
        "order_type",
        "status",
        "payment_status",
        "total",
        "amount_paid",
        "placed_at",
        "created_at",
    ]
    list_filter = [
        "status",
        "payment_status",
        "fulfillment_status",
        "order_type",
        "created_at",
    ]
    search_fields = [
        "order_number",
        "customer_email",
        "customer__email",
        "customer__first_name",
        "customer__last_name",
    ]
    readonly_fields = [
        "id",
        "order_number",
        "placed_at",
        "paid_at",
        "fulfilled_at",
        "completed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline, OrderNoteInline]
    
    fieldsets = (
        ("Order Info", {
            "fields": (
                "id",
                "order_number",
                "order_type",
                "source",
            )
        }),
        ("Customer", {
            "fields": (
                "customer",
                "customer_email",
                "customer_phone",
            )
        }),
        ("Status", {
            "fields": (
                "status",
                "payment_status",
                "fulfillment_status",
            )
        }),
        ("Totals", {
            "fields": (
                "currency",
                "subtotal",
                "discount_total",
                "tax_total",
                "shipping_total",
                "total",
                "amount_paid",
                "amount_refunded",
            )
        }),
        ("Addresses", {
            "fields": (
                "billing_address",
                "shipping_address",
            ),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": (
                "placed_at",
                "paid_at",
                "fulfilled_at",
                "completed_at",
                "cancelled_at",
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",),
        }),
        ("Notes & Metadata", {
            "fields": (
                "customer_notes",
                "internal_notes",
                "metadata",
            ),
            "classes": ("collapse",),
        }),
    )
