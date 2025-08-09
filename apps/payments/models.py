"""
Payment models for the bazary e-commerce platform.

This module contains all payment-related models including:
- PaymentMethod: User payment methods (cards, wallets)
- PaymentProvider: Payment gateway configurations
- Transaction: Payment transaction records
- Cart: Shopping cart functionality
- CartItem: Individual items in shopping cart
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.products.models import Product, ProductVariant

User = get_user_model()


class PaymentProvider(TimeStampedModel):
    """
    Payment provider configuration model.

    Stores configuration for different payment gateways like Stripe, PayPal, etc.
    """

    class ProviderType(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        PAYPAL = "paypal", "PayPal"
        RAZORPAY = "razorpay", "Razorpay"
        FLUTTERWAVE = "flutterwave", "Flutterwave"
        PAYSTACK = "paystack", "Paystack"
        CHAPA = "chapa", "Chapa"  # Ethiopian payment gateway

    name = models.CharField(max_length=100, unique=True, help_text="Provider name")
    provider_type = models.CharField(
        max_length=20,
        choices=ProviderType.choices,
        help_text="Type of payment provider",
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether provider is active"
    )
    api_key = models.CharField(max_length=200, help_text="API key for provider")
    secret_key = models.CharField(max_length=200, help_text="Secret key for provider")
    webhook_secret = models.CharField(
        max_length=200, blank=True, help_text="Webhook secret for provider"
    )
    test_mode = models.BooleanField(default=True, help_text="Whether to use test mode")
    supported_currencies = models.JSONField(
        default=list, help_text="List of supported currencies"
    )
    configuration = models.JSONField(
        default=dict, help_text="Additional provider configuration"
    )

    class Meta:
        verbose_name = "Payment Provider"
        verbose_name_plural = "Payment Providers"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class PaymentMethod(TimeStampedModel):
    """
    User payment method model.

    Stores user payment methods like credit cards, digital wallets, etc.
    """

    class MethodType(models.TextChoices):
        CARD = "card", "Credit/Debit Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        DIGITAL_WALLET = "digital_wallet", "Digital Wallet"
        CRYPTO = "crypto", "Cryptocurrency"
        MOBILE_MONEY = "mobile_money", "Mobile Money"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        help_text="User who owns this payment method",
    )
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        help_text="Payment provider for this method",
    )
    method_type = models.CharField(
        max_length=20, choices=MethodType.choices, help_text="Type of payment method"
    )
    name = models.CharField(max_length=100, help_text="Display name for payment method")
    provider_method_id = models.CharField(
        max_length=200, help_text="Payment method ID from provider"
    )
    is_default = models.BooleanField(
        default=False, help_text="Whether this is the default payment method"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether payment method is active"
    )
    metadata = models.JSONField(
        default=dict, help_text="Additional payment method metadata"
    )

    # Card-specific fields
    last_four = models.CharField(
        max_length=4, blank=True, help_text="Last four digits of card (for display)"
    )
    card_brand = models.CharField(
        max_length=20, blank=True, help_text="Card brand (Visa, Mastercard, etc.)"
    )
    expires_at = models.DateField(
        null=True, blank=True, help_text="Card expiration date"
    )

    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_payment_method_per_user",
            )
        ]

    def __str__(self):
        if self.last_four:
            return f"{self.name} ****{self.last_four}"
        return self.name

    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).exclude(
                pk=self.pk
            ).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(TimeStampedModel):
    """
    Payment transaction model.

    Records all payment transactions including successful, failed, and pending transactions.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"

    class TransactionType(models.TextChoices):
        PAYMENT = "payment", "Payment"
        REFUND = "refund", "Refund"
        PARTIAL_REFUND = "partial_refund", "Partial Refund"
        CHARGEBACK = "chargeback", "Chargeback"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique transaction ID",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="User who made the transaction",
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Payment method used for transaction",
    )
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="Payment provider used",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.PAYMENT,
        help_text="Type of transaction",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current transaction status",
    )

    # Amount fields
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Transaction amount",
    )
    currency = models.CharField(
        max_length=3, default="USD", help_text="Currency code (ISO 4217)"
    )

    # Provider-specific fields
    provider_transaction_id = models.CharField(
        max_length=200, unique=True, help_text="Transaction ID from payment provider"
    )
    provider_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Fee charged by payment provider",
    )

    # Transaction details
    description = models.TextField(blank=True, help_text="Transaction description")
    reference = models.CharField(
        max_length=100, blank=True, help_text="Internal reference number"
    )

    # Timing fields
    processed_at = models.DateTimeField(
        null=True, blank=True, help_text="When transaction was processed"
    )
    failed_at = models.DateTimeField(
        null=True, blank=True, help_text="When transaction failed"
    )

    # Metadata and error handling
    metadata = models.JSONField(
        default=dict, help_text="Additional transaction metadata"
    )
    error_message = models.TextField(
        blank=True, help_text="Error message if transaction failed"
    )
    webhook_data = models.JSONField(
        default=dict, help_text="Raw webhook data from provider"
    )

    # Related transaction (for refunds)
    parent_transaction = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_transactions",
        help_text="Parent transaction (for refunds)",
    )

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["provider_transaction_id"]),
        ]

    def __str__(self):
        return f"Transaction {self.id} - {self.amount} {self.currency} ({self.status})"

    def mark_as_succeeded(self):
        """Mark transaction as succeeded."""
        self.status = self.Status.SUCCEEDED
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at"])

    def mark_as_failed(self, error_message=""):
        """Mark transaction as failed."""
        self.status = self.Status.FAILED
        self.failed_at = timezone.now()
        if error_message:
            self.error_message = error_message
        self.save(update_fields=["status", "failed_at", "error_message"])

    @property
    def is_successful(self):
        """Check if transaction is successful."""
        return self.status == self.Status.SUCCEEDED

    @property
    def is_refundable(self):
        """Check if transaction can be refunded."""
        return (
            self.is_successful
            and self.transaction_type == self.TransactionType.PAYMENT
            and not self.child_transactions.filter(
                transaction_type__in=[
                    self.TransactionType.REFUND,
                    self.TransactionType.PARTIAL_REFUND,
                ]
            ).exists()
        )


class Cart(TimeStampedModel):
    """
    Shopping cart model.

    Represents a user's shopping cart containing multiple items.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ABANDONED = "abandoned", "Abandoned"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique cart ID"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        help_text="User who owns the cart (null for guest carts)",
    )
    session_key = models.CharField(
        max_length=40, blank=True, help_text="Session key for guest carts"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Current cart status",
    )
    currency = models.CharField(
        max_length=3, default="USD", help_text="Cart currency (ISO 4217)"
    )

    # Pricing fields (calculated)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Subtotal amount (before tax and shipping)",
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Tax amount"
    )
    shipping_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Shipping amount",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Discount amount",
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total amount",
    )

    # Cart metadata
    notes = models.TextField(blank=True, help_text="Customer notes for the cart")
    metadata = models.JSONField(default=dict, help_text="Additional cart metadata")

    # Expiry handling
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="When the cart expires"
    )

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["session_key", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        if self.user:
            return f"Cart {self.id} - {self.user.email}"
        return f"Guest Cart {self.id}"

    @property
    def item_count(self):
        """Get total number of items in cart."""
        return self.items.aggregate(total=models.Sum("quantity"))["total"] or 0

    @property
    def is_empty(self):
        """Check if cart is empty."""
        return self.item_count == 0

    def calculate_totals(self):
        """Calculate and update cart totals."""
        items = self.items.select_related("product", "variant")

        subtotal = Decimal("0.00")
        for item in items:
            subtotal += item.line_total

        self.subtotal = subtotal
        # Tax and shipping calculation would be done here
        # For now, we'll set them to 0
        self.tax_amount = Decimal("0.00")
        self.shipping_amount = Decimal("0.00")

        self.total = (
            self.subtotal
            + self.tax_amount
            + self.shipping_amount
            - self.discount_amount
        )
        self.save(update_fields=["subtotal", "tax_amount", "shipping_amount", "total"])

    def clear(self):
        """Clear all items from cart."""
        self.items.all().delete()
        self.calculate_totals()

    def merge_with_cart(self, other_cart):
        """Merge another cart into this cart."""
        for item in other_cart.items.all():
            existing_item = self.items.filter(
                product=item.product, variant=item.variant
            ).first()

            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                item.cart = self
                item.save()

        other_cart.delete()
        self.calculate_totals()


class CartItem(TimeStampedModel):
    """
    Cart item model.

    Represents individual items in a shopping cart.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Cart containing this item",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        help_text="Product in cart",
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
        help_text="Product variant (if applicable)",
    )
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], help_text="Quantity of items"
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unit price at time of adding to cart",
    )
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Total price for this line item"
    )

    # Item metadata
    custom_attributes = models.JSONField(
        default=dict, help_text="Custom attributes for the item"
    )
    notes = models.TextField(blank=True, help_text="Customer notes for this item")

    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product", "variant"],
                name="unique_cart_product_variant",
            ),
            models.UniqueConstraint(
                fields=["cart", "product"],
                condition=models.Q(variant__isnull=True),
                name="unique_cart_product_no_variant",
            ),
        ]

    def __str__(self):
        if self.variant:
            return f"{self.product.name} ({self.variant}) x{self.quantity}"
        return f"{self.product.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        # Calculate line total
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

        # Update cart totals
        self.cart.calculate_totals()

    def delete(self, *args, **kwargs):
        cart = self.cart
        super().delete(*args, **kwargs)
        # Update cart totals after deletion
        cart.calculate_totals()

    @property
    def display_name(self):
        """Get display name for the item."""
        if self.variant:
            return f"{self.product.name} - {self.variant}"
        return self.product.name

    def update_quantity(self, quantity):
        """Update item quantity."""
        self.quantity = max(1, quantity)
        self.save()

    def is_available(self):
        """Check if item is still available."""
        if self.variant:
            return (
                self.variant.is_active and self.variant.stock_quantity >= self.quantity
            )
        return self.product.is_active and (
            not self.product.track_inventory
            or self.product.stock_quantity >= self.quantity
        )
