"""
Payment serializers with comprehensive Swagger/OpenAPI documentation.

This module contains all payment-related serializers including:
- PaymentProviderSerializer: Payment provider configuration
- PaymentMethodSerializer: User payment methods
- TransactionSerializer: Payment transactions
- CartSerializer: Shopping cart management
- CartItemSerializer: Individual cart items
"""

from decimal import Decimal

from django.utils import timezone

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.serializers.base import ProductListSerializer
from apps.products.serializers.variants import ProductVariantListSerializer

from .models import Cart, CartItem, PaymentMethod, PaymentProvider, Transaction


class PaymentProviderSerializer(serializers.ModelSerializer):
    """
    Payment provider serializer for API responses.

    Used for listing available payment providers to users.
    Excludes sensitive configuration data.
    """

    class Meta:
        model = PaymentProvider
        fields = [
            "id",
            "name",
            "provider_type",
            "is_active",
            "supported_currencies",
            "test_mode",
        ]
        read_only_fields = ["id"]


class PaymentProviderDetailSerializer(serializers.ModelSerializer):
    """
    Detailed payment provider serializer for admin use.

    Includes all configuration fields for payment provider management.
    Should only be used by admin users.
    """

    class Meta:
        model = PaymentProvider
        fields = [
            "id",
            "name",
            "provider_type",
            "is_active",
            "api_key",
            "secret_key",
            "webhook_secret",
            "test_mode",
            "supported_currencies",
            "configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "api_key": {"write_only": True},
            "secret_key": {"write_only": True},
            "webhook_secret": {"write_only": True},
        }


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Payment method serializer for user payment methods.

    Used for managing user payment methods like credit cards, wallets, etc.
    Excludes sensitive payment data for security.
    """

    provider_name = serializers.CharField(source="provider.name", read_only=True)
    provider_type = serializers.CharField(
        source="provider.provider_type", read_only=True
    )
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "provider",
            "provider_name",
            "provider_type",
            "method_type",
            "name",
            "is_default",
            "is_active",
            "last_four",
            "card_brand",
            "expires_at",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "provider_name",
            "provider_type",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "provider_method_id": {"write_only": True},
        }

    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj):
        """Check if payment method is expired."""
        if obj.expires_at:
            from django.utils import timezone

            return obj.expires_at < timezone.now().date()
        return False

    def validate(self, attrs):
        """Validate payment method data."""
        user = self.context["request"].user

        # Check if user is trying to set multiple default payment methods
        if attrs.get("is_default") and not self.instance:
            existing_default = PaymentMethod.objects.filter(
                user=user, is_default=True
            ).exists()
            if existing_default:
                attrs["is_default"] = False

        return attrs

    def create(self, validated_data):
        """Create payment method for the current user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """
    Payment method creation serializer.

    Used for creating new payment methods with provider tokens.
    """

    provider_token = serializers.CharField(
        write_only=True, help_text="Payment token from the payment provider"
    )

    class Meta:
        model = PaymentMethod
        fields = [
            "provider",
            "method_type",
            "name",
            "is_default",
            "provider_token",
        ]

    def create(self, validated_data):
        """Create payment method with provider token."""
        provider_token = validated_data.pop("provider_token")
        validated_data["user"] = self.context["request"].user

        # Here you would integrate with the payment provider
        # to create the payment method using the token
        # For now, we'll create a placeholder implementation
        validated_data["provider_method_id"] = f"pm_{provider_token[:10]}"

        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Transaction serializer for payment transaction records.

    Used for displaying transaction history and details to users.
    """

    user_email = serializers.CharField(source="user.email", read_only=True)
    payment_method_name = serializers.CharField(
        source="payment_method.name", read_only=True
    )
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    is_refundable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "user_email",
            "payment_method_name",
            "provider_name",
            "transaction_type",
            "status",
            "amount",
            "currency",
            "provider_fee",
            "description",
            "reference",
            "processed_at",
            "failed_at",
            "error_message",
            "is_refundable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "payment_method_name",
            "provider_name",
            "is_refundable",
            "created_at",
            "updated_at",
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    """
    Transaction creation serializer.

    Used for creating new payment transactions.
    """

    class Meta:
        model = Transaction
        fields = [
            "payment_method",
            "provider",
            "amount",
            "currency",
            "description",
            "reference",
            "metadata",
        ]

    def validate_amount(self, value):
        """Validate transaction amount."""
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate(self, attrs):
        """Validate transaction data."""
        user = self.context["request"].user
        payment_method = attrs.get("payment_method")

        # Ensure payment method belongs to the user
        if payment_method and payment_method.user != user:
            raise serializers.ValidationError(
                "Payment method does not belong to the current user."
            )

        # Ensure payment method is active
        if payment_method and not payment_method.is_active:
            raise serializers.ValidationError("Payment method is not active.")

        return attrs

    def create(self, validated_data):
        """Create transaction for the current user."""
        validated_data["user"] = self.context["request"].user
        validated_data["provider_transaction_id"] = (
            f"txn_{self.context['request'].user.id}_{timezone.now().timestamp()}"
        )
        return super().create(validated_data)


class RefundTransactionSerializer(serializers.Serializer):
    """
    Serializer for refund transaction requests.

    Used for processing refund requests on existing transactions.
    """

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Refund amount (leave empty for full refund)",
    )
    reason = serializers.CharField(
        max_length=500, required=False, help_text="Reason for refund"
    )

    def validate_amount(self, value):
        """Validate refund amount."""
        if value is not None and value <= Decimal("0.00"):
            raise serializers.ValidationError(
                "Refund amount must be greater than zero."
            )
        return value

    def validate(self, attrs):
        """Validate refund request."""
        transaction = self.context["transaction"]
        amount = attrs.get("amount")

        if not transaction.is_refundable:
            raise serializers.ValidationError("Transaction is not refundable.")

        if amount and amount > transaction.amount:
            raise serializers.ValidationError(
                "Refund amount cannot exceed original transaction amount."
            )

        return attrs


class PaymentInitiationSerializer(serializers.Serializer):
    """
    Serializer for initiating a payment with a provider (default: Chapa).
    Allows either direct amount/currency or using an existing Cart ID to derive totals.
    """

    provider = serializers.PrimaryKeyRelatedField(
        queryset=PaymentProvider.objects.filter(is_active=True),
        required=False,
        help_text="Payment provider ID (defaults to active Chapa provider)",
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Payment amount when not using a cart",
    )
    currency = serializers.CharField(
        max_length=3,
        required=False,
        default="ETB",
        help_text="Currency code (ISO 4217), defaults to ETB",
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Payment description",
    )
    reference = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Your internal reference (e.g., ORDER-123)",
    )
    metadata = serializers.DictField(
        required=False,
        default=dict,
        help_text="Additional metadata to pass to the provider",
    )
    cart_id = serializers.UUIDField(
        required=False,
        help_text="Cart ID to derive amount/description automatically",
    )

    def validate(self, attrs):
        user = self.context["request"].user
        amount = attrs.get("amount")
        cart_id = attrs.get("cart_id")

        if not amount and not cart_id:
            raise serializers.ValidationError("Provide either amount or cart_id.")

        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                raise serializers.ValidationError("Cart not found.")
            # If cart is tied to a user, ensure current user owns it
            if cart.user and cart.user != user:
                raise serializers.ValidationError("You do not own this cart.")
            # Ensure totals are up-to-date
            cart.calculate_totals()
            attrs["amount"] = cart.total
            attrs.setdefault("currency", cart.currency)
            attrs.setdefault(
                "description", attrs.get("description") or f"Cart payment {cart.id}"
            )
            # Attach cart id into metadata for traceability
            meta = attrs.get("metadata", {})
            meta.update({"cart_id": str(cart.id)})
            attrs["metadata"] = meta

        # Default provider to active Chapa if not provided
        if not attrs.get("provider"):
            try:
                attrs["provider"] = PaymentProvider.objects.get(
                    provider_type=PaymentProvider.ProviderType.CHAPA,
                    is_active=True,
                )
            except PaymentProvider.DoesNotExist:
                raise serializers.ValidationError(
                    "Active Chapa provider not configured."
                )

        if attrs["amount"] <= Decimal("0.00"):
            raise serializers.ValidationError("Amount must be greater than zero.")

        return attrs


class PaymentVerificationRequestSerializer(serializers.Serializer):
    """Serializer for verifying a payment by transaction id (tx_ref)."""

    tx_ref = serializers.UUIDField(help_text="Transaction ID (UUID)")


class PaymentInitiationResponseSerializer(serializers.Serializer):
    """Serializer for payment initiation response payload."""

    transaction_id = serializers.UUIDField()
    status = serializers.CharField()
    checkout_url = serializers.CharField(allow_blank=True)
    provider = serializers.CharField()
    message = serializers.CharField()


class CartItemSerializer(serializers.ModelSerializer):
    """
    Cart item serializer for shopping cart items.

    Used for managing individual items within a shopping cart.
    """

    product = ProductListSerializer(read_only=True)
    variant = ProductVariantListSerializer(read_only=True)
    display_name = serializers.CharField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "variant",
            "quantity",
            "unit_price",
            "line_total",
            "display_name",
            "is_available",
            "custom_attributes",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "line_total",
            "display_name",
            "is_available",
            "created_at",
            "updated_at",
        ]

    def validate_quantity(self, value):
        """Validate item quantity."""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class CartItemCreateSerializer(serializers.ModelSerializer):
    """
    Cart item creation serializer.

    Used for adding new items to a shopping cart.
    """

    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = CartItem
        fields = [
            "product_id",
            "variant_id",
            "quantity",
            "custom_attributes",
            "notes",
        ]

    def validate(self, attrs):
        """Validate cart item creation."""
        from apps.products.models import Product, ProductVariant

        product_id = attrs.get("product_id")
        variant_id = attrs.get("variant_id")
        quantity = attrs.get("quantity", 1)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id, product=product, is_active=True
                )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    "Product variant not found or inactive."
                )

        # Check stock availability
        if variant:
            if variant.stock_quantity < quantity:
                raise serializers.ValidationError(
                    "Not enough stock available for variant."
                )
            attrs["unit_price"] = variant.price
        else:
            if product.track_inventory and product.stock_quantity < quantity:
                raise serializers.ValidationError(
                    "Not enough stock available for product."
                )
            attrs["unit_price"] = product.price

        attrs["product"] = product
        attrs["variant"] = variant

        return attrs

    def create(self, validated_data):
        """Create cart item."""
        validated_data.pop("product_id")
        validated_data.pop("variant_id", None)
        return super().create(validated_data)


class CartSerializer(serializers.ModelSerializer):
    """
    Shopping cart serializer.

    Used for managing user shopping carts with comprehensive item details.
    """

    items = CartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "user_email",
            "status",
            "currency",
            "subtotal",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total",
            "item_count",
            "is_empty",
            "notes",
            "expires_at",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user_email",
            "subtotal",
            "tax_amount",
            "shipping_amount",
            "total",
            "item_count",
            "is_empty",
            "created_at",
            "updated_at",
        ]


class CartCreateSerializer(serializers.ModelSerializer):
    """
    Cart creation serializer.

    Used for creating new shopping carts.
    """

    class Meta:
        model = Cart
        fields = [
            "currency",
            "notes",
        ]

    def create(self, validated_data):
        """Create cart for the current user."""
        user = self.context["request"].user

        # Check if user already has an active cart
        existing_cart = Cart.objects.filter(
            user=user, status=Cart.Status.ACTIVE
        ).first()

        if existing_cart:
            return existing_cart

        validated_data["user"] = user
        return super().create(validated_data)


class AddToCartSerializer(serializers.Serializer):
    """
    Add to cart serializer.

    Used for adding products to an existing shopping cart.
    """

    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, default=1)
    custom_attributes = serializers.JSONField(required=False, default=dict)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        """Validate add to cart request."""
        from apps.products.models import Product, ProductVariant

        product_id = attrs["product_id"]
        variant_id = attrs.get("variant_id")
        quantity = attrs["quantity"]

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive.")

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id, product=product, is_active=True
                )
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    "Product variant not found or inactive."
                )

        # Check stock availability
        if variant:
            if variant.stock_quantity < quantity:
                raise serializers.ValidationError(
                    "Not enough stock available for variant."
                )
        else:
            if product.track_inventory and product.stock_quantity < quantity:
                raise serializers.ValidationError(
                    "Not enough stock available for product."
                )

        attrs["product"] = product
        attrs["variant"] = variant

        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Update cart item serializer.

    Used for updating quantity and attributes of cart items.
    """

    quantity = serializers.IntegerField(min_value=1)
    custom_attributes = serializers.JSONField(required=False)
    notes = serializers.CharField(max_length=500, required=False)

    def validate_quantity(self, value):
        """Validate updated quantity."""
        cart_item = self.context["cart_item"]

        # Check stock availability for new quantity
        if cart_item.variant:
            if cart_item.variant.stock_quantity < value:
                raise serializers.ValidationError(
                    "Not enough stock available for variant."
                )
        else:
            if (
                cart_item.product.track_inventory
                and cart_item.product.stock_quantity < value
            ):
                raise serializers.ValidationError(
                    "Not enough stock available for product."
                )

        return value


class CartSummarySerializer(serializers.ModelSerializer):
    """
    Cart summary serializer.

    Used for displaying cart totals and basic information without full item details.
    """

    item_count = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "status",
            "currency",
            "subtotal",
            "tax_amount",
            "shipping_amount",
            "discount_amount",
            "total",
            "item_count",
            "is_empty",
        ]
        read_only_fields = ["id"]
