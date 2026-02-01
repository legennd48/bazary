"""
Order Models.

Comprehensive order management with Shopify-level clarity and completeness.
"""

import uuid
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    """
    Order status workflow.
    
    Shopify-like clarity: each status has clear meaning and transitions.
    """
    # Initial states
    DRAFT = "draft", "Draft"  # Order being built (cart conversion)
    PENDING = "pending", "Pending"  # Awaiting payment
    
    # Payment states
    PAYMENT_PENDING = "payment_pending", "Payment Pending"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    PAID = "paid", "Paid"  # Payment confirmed
    
    # Fulfillment states (for physical products)
    PROCESSING = "processing", "Processing"
    PARTIALLY_FULFILLED = "partially_fulfilled", "Partially Fulfilled"
    FULFILLED = "fulfilled", "Fulfilled"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    
    # Completion states
    COMPLETED = "completed", "Completed"
    
    # Cancellation/refund states
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"


class FulfillmentStatus(models.TextChoices):
    """Fulfillment status for order items."""
    UNFULFILLED = "unfulfilled", "Unfulfilled"
    PARTIALLY_FULFILLED = "partially_fulfilled", "Partially Fulfilled"
    FULFILLED = "fulfilled", "Fulfilled"
    SCHEDULED = "scheduled", "Scheduled"  # For services/bookings


class PaymentStatus(models.TextChoices):
    """Payment status for orders."""
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    PAID = "paid", "Paid"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    REFUNDED = "refunded", "Refunded"
    VOIDED = "voided", "Voided"


class OrderType(models.TextChoices):
    """Type of order."""
    PRODUCT = "product", "Product Order"
    SERVICE = "service", "Service Order"
    BOOKING = "booking", "Booking Order"
    MIXED = "mixed", "Mixed Order"


class Order(TimeStampedModel):
    """
    Core order model.
    
    Represents a complete order with items, totals, and status tracking.
    This is the canonical record of commerce for the platform.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique order identifier",
    )
    
    # Order number (human-readable, sequential per client)
    order_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Human-readable order number (e.g., ORD-2024-00001)",
    )
    
    # Customer
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
        help_text="Customer who placed the order (null for guest checkout)",
    )
    customer_email = models.EmailField(
        help_text="Customer email (stored for guest orders and notifications)",
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Customer phone number",
    )
    
    # Order type and status
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.PRODUCT,
        help_text="Type of order",
    )
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        db_index=True,
        help_text="Current order status",
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
        help_text="Payment status",
    )
    fulfillment_status = models.CharField(
        max_length=30,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.UNFULFILLED,
        db_index=True,
        help_text="Fulfillment status",
    )
    
    # Pricing (all amounts in smallest currency unit or decimal)
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code (ISO 4217)",
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Subtotal before discounts, tax, shipping",
    )
    discount_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total discount amount",
    )
    tax_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total tax amount",
    )
    shipping_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total shipping cost",
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Final total amount",
    )
    
    # Payment tracking
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Amount paid so far",
    )
    amount_refunded = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Amount refunded",
    )
    
    # Addresses (stored as JSON for flexibility and history)
    billing_address = models.JSONField(
        default=dict,
        blank=True,
        help_text="Billing address snapshot",
    )
    shipping_address = models.JSONField(
        default=dict,
        blank=True,
        help_text="Shipping address snapshot",
    )
    
    # Timestamps
    placed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was placed (checkout completed)",
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was confirmed",
    )
    fulfilled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was fully fulfilled",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was completed",
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When order was cancelled",
    )
    
    # Notes and metadata
    customer_notes = models.TextField(
        blank=True,
        help_text="Notes from customer",
    )
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes (not visible to customer)",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata",
    )
    
    # Source tracking
    source = models.CharField(
        max_length=50,
        default="web",
        help_text="Order source (web, mobile, api, admin)",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of order placement",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string",
    )
    
    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["fulfillment_status"]),
            models.Index(fields=["placed_at"]),
        ]
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not set."""
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)
    
    def _generate_order_number(self) -> str:
        """Generate a unique order number."""
        from django.conf import settings
        prefix = getattr(settings, "CLIENT_CONFIG", {}).get("order_number_prefix", "ORD")
        year = timezone.now().year
        
        # Get the next sequence number
        last_order = Order.objects.filter(
            order_number__startswith=f"{prefix}-{year}-"
        ).order_by("-order_number").first()
        
        if last_order:
            try:
                last_seq = int(last_order.order_number.split("-")[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        
        return f"{prefix}-{year}-{seq:05d}"
    
    @property
    def is_paid(self) -> bool:
        """Check if order is fully paid."""
        return self.payment_status == PaymentStatus.PAID
    
    @property
    def is_fulfilled(self) -> bool:
        """Check if order is fully fulfilled."""
        return self.fulfillment_status == FulfillmentStatus.FULFILLED
    
    @property
    def can_cancel(self) -> bool:
        """Check if order can be cancelled."""
        non_cancellable = {
            OrderStatus.CANCELLED,
            OrderStatus.REFUNDED,
            OrderStatus.COMPLETED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        }
        return self.status not in non_cancellable
    
    @property
    def can_refund(self) -> bool:
        """Check if order can be refunded."""
        return (
            self.payment_status in {PaymentStatus.PAID, PaymentStatus.PARTIALLY_REFUNDED}
            and self.amount_paid > self.amount_refunded
        )
    
    @property
    def balance_due(self) -> Decimal:
        """Calculate remaining balance."""
        return max(Decimal("0.00"), self.total - self.amount_paid + self.amount_refunded)
    
    def calculate_totals(self) -> None:
        """Recalculate order totals from items."""
        items = self.items.all()
        self.subtotal = sum(item.subtotal for item in items)
        # discount_total, tax_total, shipping_total set separately
        self.total = (
            self.subtotal 
            - self.discount_total 
            + self.tax_total 
            + self.shipping_total
        )


class OrderItem(TimeStampedModel):
    """
    Individual item in an order.
    
    Can reference products, variants, services, or bookings.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent order",
    )
    
    # Item type
    class ItemType(models.TextChoices):
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"
        BOOKING = "booking", "Booking"
        FEE = "fee", "Fee"
        DISCOUNT = "discount", "Discount"
    
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.PRODUCT,
        help_text="Type of line item",
    )
    
    # Product reference (nullable - for non-product items)
    product_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to product (if product item)",
    )
    variant_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to product variant (if applicable)",
    )
    
    # Service reference
    service_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to service (if service item)",
    )
    
    # Booking reference
    booking_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Reference to booking (if booking item)",
    )
    
    # Item details (snapshot at time of order)
    name = models.CharField(
        max_length=500,
        help_text="Item name (snapshot)",
    )
    sku = models.CharField(
        max_length=100,
        blank=True,
        help_text="SKU (snapshot)",
    )
    description = models.TextField(
        blank=True,
        help_text="Item description",
    )
    
    # Variant options (snapshot)
    variant_options = models.JSONField(
        default=dict,
        blank=True,
        help_text="Variant options snapshot (e.g., {size: 'M', color: 'Blue'})",
    )
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Unit price at time of order",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity ordered",
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Discount on this item",
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Tax on this item",
    )
    
    # Fulfillment
    quantity_fulfilled = models.PositiveIntegerField(
        default=0,
        help_text="Quantity fulfilled so far",
    )
    fulfillment_status = models.CharField(
        max_length=30,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.UNFULFILLED,
        help_text="Item fulfillment status",
    )
    
    # For digital/service items
    requires_shipping = models.BooleanField(
        default=True,
        help_text="Whether this item requires shipping",
    )
    is_digital = models.BooleanField(
        default=False,
        help_text="Whether this is a digital item",
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional item metadata",
    )
    
    class Meta:
        db_table = "order_items"
        ordering = ["created_at"]
    
    def __str__(self):
        return f"{self.name} x{self.quantity}"
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.unit_price * self.quantity
    
    @property
    def total(self) -> Decimal:
        """Calculate item total with discounts and tax."""
        return self.subtotal - self.discount_amount + self.tax_amount
    
    @property
    def is_fulfilled(self) -> bool:
        """Check if item is fully fulfilled."""
        return self.quantity_fulfilled >= self.quantity


class OrderStatusHistory(TimeStampedModel):
    """
    Track order status changes for audit trail.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    
    from_status = models.CharField(
        max_length=30,
        blank=True,
        help_text="Previous status",
    )
    to_status = models.CharField(
        max_length=30,
        help_text="New status",
    )
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
        help_text="User who made the change",
    )
    
    reason = models.TextField(
        blank=True,
        help_text="Reason for status change",
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
    )
    
    class Meta:
        db_table = "order_status_history"
        ordering = ["-created_at"]
        verbose_name_plural = "Order status histories"
    
    def __str__(self):
        return f"{self.order.order_number}: {self.from_status} -> {self.to_status}"


class OrderNote(TimeStampedModel):
    """
    Notes attached to orders.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_notes",
    )
    
    content = models.TextField(
        help_text="Note content",
    )
    
    is_customer_visible = models.BooleanField(
        default=False,
        help_text="Whether customer can see this note",
    )
    
    class Meta:
        db_table = "order_notes"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Note on {self.order.order_number}"
