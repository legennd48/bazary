"""
Order Serializers.

API serializers for order management.
"""

from decimal import Decimal
from typing import Dict

from rest_framework import serializers

from .models import (
    FulfillmentStatus,
    Order,
    OrderItem,
    OrderNote,
    OrderStatus,
    OrderStatusHistory,
    OrderType,
    PaymentStatus,
)


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    
    subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    is_fulfilled = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_type",
            "product_id",
            "variant_id",
            "service_id",
            "booking_id",
            "name",
            "sku",
            "description",
            "variant_options",
            "unit_price",
            "quantity",
            "discount_amount",
            "tax_amount",
            "subtotal",
            "total",
            "quantity_fulfilled",
            "fulfillment_status",
            "requires_shipping",
            "is_digital",
            "metadata",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "quantity_fulfilled",
            "fulfillment_status",
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""
    
    item_type = serializers.ChoiceField(
        choices=OrderItem.ItemType.choices,
        default=OrderItem.ItemType.PRODUCT,
    )
    product_id = serializers.UUIDField(required=False, allow_null=True)
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    service_id = serializers.UUIDField(required=False, allow_null=True)
    booking_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=500)
    sku = serializers.CharField(max_length=100, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    variant_options = serializers.DictField(required=False, default=dict)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    quantity = serializers.IntegerField(min_value=1, default=1)
    requires_shipping = serializers.BooleanField(default=True)
    is_digital = serializers.BooleanField(default=False)
    metadata = serializers.DictField(required=False, default=dict)


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history."""
    
    changed_by_email = serializers.EmailField(
        source="changed_by.email", read_only=True
    )
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "changed_by",
            "changed_by_email",
            "reason",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class OrderNoteSerializer(serializers.ModelSerializer):
    """Serializer for order notes."""
    
    author_email = serializers.EmailField(source="author.email", read_only=True)
    
    class Meta:
        model = OrderNote
        fields = [
            "id",
            "author",
            "author_email",
            "content",
            "is_customer_visible",
            "created_at",
        ]
        read_only_fields = ["id", "author", "created_at"]


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view (minimal fields)."""
    
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_email",
            "order_type",
            "status",
            "payment_status",
            "fulfillment_status",
            "currency",
            "total",
            "amount_paid",
            "item_count",
            "placed_at",
            "created_at",
        ]
        read_only_fields = fields
    
    def get_item_count(self, obj) -> int:
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    notes = serializers.SerializerMethodField()
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    can_cancel = serializers.BooleanField(read_only=True)
    can_refund = serializers.BooleanField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_fulfilled = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_email",
            "customer_phone",
            "order_type",
            "status",
            "payment_status",
            "fulfillment_status",
            "currency",
            "subtotal",
            "discount_total",
            "tax_total",
            "shipping_total",
            "total",
            "amount_paid",
            "amount_refunded",
            "balance_due",
            "billing_address",
            "shipping_address",
            "placed_at",
            "paid_at",
            "fulfilled_at",
            "completed_at",
            "cancelled_at",
            "customer_notes",
            "source",
            "can_cancel",
            "can_refund",
            "is_paid",
            "is_fulfilled",
            "items",
            "status_history",
            "notes",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
    
    def get_notes(self, obj):
        """Get notes visible to current user."""
        request = self.context.get("request")
        notes = obj.notes.all()
        
        # Staff sees all notes, customers only see customer-visible ones
        if request and request.user.is_staff:
            return OrderNoteSerializer(notes, many=True).data
        else:
            visible_notes = notes.filter(is_customer_visible=True)
            return OrderNoteSerializer(visible_notes, many=True).data


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders."""
    
    customer_email = serializers.EmailField(required=False)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=3, default="USD")
    billing_address = serializers.DictField(required=False, default=dict)
    shipping_address = serializers.DictField(required=False, default=dict)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    items = OrderItemCreateSerializer(many=True, required=False)
    metadata = serializers.DictField(required=False, default=dict)
    
    def validate_items(self, value):
        """Validate items list."""
        if not value:
            return value
        
        for item in value:
            if item.get("unit_price", 0) < 0:
                raise serializers.ValidationError("Unit price cannot be negative")
            if item.get("quantity", 1) < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
        
        return value
    
    def create(self, validated_data):
        """Create order using service."""
        from .services import OrderService
        
        request = self.context.get("request")
        items = validated_data.pop("items", [])
        
        # Get customer from request if authenticated
        customer = None
        if request and request.user.is_authenticated:
            customer = request.user
            if not validated_data.get("customer_email"):
                validated_data["customer_email"] = customer.email
        
        # Get IP address
        ip_address = None
        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")
        
        return OrderService.create_order(
            customer=customer,
            items=items,
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            **validated_data,
        )


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout from cart."""
    
    cart_id = serializers.UUIDField(required=False, help_text="Cart ID (optional if user has active cart)")
    billing_address = serializers.DictField(required=True)
    shipping_address = serializers.DictField(required=False)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    same_as_billing = serializers.BooleanField(
        default=False,
        help_text="Use billing address as shipping address",
    )
    
    def validate(self, attrs):
        """Validate checkout data."""
        # If same_as_billing, copy billing to shipping
        if attrs.get("same_as_billing"):
            attrs["shipping_address"] = attrs["billing_address"]
        
        # Validate required address fields
        required_fields = ["street_address", "city", "country"]
        for field in required_fields:
            if field not in attrs.get("billing_address", {}):
                raise serializers.ValidationError(
                    {"billing_address": f"Missing required field: {field}"}
                )
        
        return attrs


class OrderActionSerializer(serializers.Serializer):
    """Serializer for order actions (cancel, refund, etc.)."""
    
    reason = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        help_text="Amount for refund actions",
    )
    metadata = serializers.DictField(required=False, default=dict)


class PaymentRecordSerializer(serializers.Serializer):
    """Serializer for recording payments against orders."""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = serializers.CharField(max_length=200, required=False)
    metadata = serializers.DictField(required=False, default=dict)
    
    def validate_amount(self, value):
        """Validate payment amount."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
