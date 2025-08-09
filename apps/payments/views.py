"""
Payment views with comprehensive Swagger/OpenAPI documentation.

This module contains all payment-related views including:
- PaymentProviderViewSet: Payment provider management
- PaymentMethodViewSet: User payment method management
- TransactionViewSet: Payment transaction handling
- CartViewSet: Shopping cart management
- CartItemViewSet: Cart item operations
"""

from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.swagger_docs import SwaggerTags


class IsUserOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission for objects that use 'user' field instead of 'owner'.
    Works for PaymentMethod, Transaction, Cart, etc.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for the object owner
        return obj.user == request.user


from .models import Cart, CartItem, PaymentMethod, PaymentProvider, Transaction
from .serializers import (
    AddToCartSerializer,
    CartCreateSerializer,
    CartItemCreateSerializer,
    CartItemSerializer,
    CartSerializer,
    CartSummarySerializer,
    PaymentInitiationResponseSerializer,
    PaymentInitiationSerializer,
    PaymentMethodCreateSerializer,
    PaymentMethodSerializer,
    PaymentProviderSerializer,
    PaymentVerificationRequestSerializer,
    RefundTransactionSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
    UpdateCartItemSerializer,
)
from .services.factory import get_payment_service_from_provider


@extend_schema_view(
    list=extend_schema(
        summary="List payment providers",
        description="Get a list of available payment providers and their supported features.",
        responses={
            200: OpenApiResponse(
                response=PaymentProviderSerializer(many=True),
                description="List of payment providers",
                examples=[
                    OpenApiExample(
                        "Payment Providers",
                        value=[
                            {
                                "id": 1,
                                "name": "Stripe",
                                "provider_type": "stripe",
                                "is_active": True,
                                "supported_currencies": ["USD", "EUR", "GBP"],
                                "test_mode": True,
                            },
                            {
                                "id": 2,
                                "name": "PayPal",
                                "provider_type": "paypal",
                                "is_active": True,
                                "supported_currencies": ["USD", "EUR"],
                                "test_mode": True,
                            },
                        ],
                    )
                ],
            )
        },
        tags=[SwaggerTags.PAYMENT_PROVIDERS],
    ),
    retrieve=extend_schema(
        summary="Get payment provider details",
        description="Get detailed information about a specific payment provider.",
        responses={
            200: PaymentProviderSerializer,
            404: OpenApiResponse(description="Payment provider not found"),
        },
        tags=[SwaggerTags.PAYMENT_PROVIDERS],
    ),
)
class PaymentProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ## Payment Provider Information

    Get information about available payment providers and their capabilities.

    ### 💳 Features
    - **Provider List**: View all active payment providers
    - **Provider Details**: Get detailed information about specific providers
    - **Configuration**: See supported payment methods and currencies
    - **Status**: Only active and available providers are shown

    ### 🔐 Access
    - Authenticated users only
    - Read-only access to provider information
    """

    queryset = PaymentProvider.objects.filter(is_active=True)
    serializer_class = PaymentProviderSerializer
    permission_classes = [IsAuthenticated]


@extend_schema_view(
    list=extend_schema(
        summary="List user payment methods",
        description="Get a list of the current user's saved payment methods.",
        responses={
            200: OpenApiResponse(
                response=PaymentMethodSerializer(many=True),
                description="List of user payment methods",
                examples=[
                    OpenApiExample(
                        "Payment Methods",
                        value=[
                            {
                                "id": 1,
                                "provider": 1,
                                "provider_name": "Stripe",
                                "provider_type": "stripe",
                                "method_type": "card",
                                "name": "Personal Visa Card",
                                "is_default": True,
                                "is_active": True,
                                "last_four": "4242",
                                "card_brand": "visa",
                                "expires_at": "2026-12-31",
                                "is_expired": False,
                                "created_at": "2025-08-09T10:00:00Z",
                                "updated_at": "2025-08-09T10:00:00Z",
                            }
                        ],
                    )
                ],
            )
        },
        tags=[SwaggerTags.PAYMENT_METHODS],
    ),
    create=extend_schema(
        summary="Add new payment method",
        description="Add a new payment method for the current user using a payment token from the provider.",
        request=PaymentMethodCreateSerializer,
        responses={
            201: PaymentMethodSerializer,
            400: OpenApiResponse(description="Invalid payment method data"),
        },
        examples=[
            OpenApiExample(
                "Create Payment Method",
                value={
                    "provider": 1,
                    "method_type": "card",
                    "name": "Personal Visa Card",
                    "is_default": True,
                    "provider_token": "tok_1234567890abcdef",
                },
            )
        ],
        tags=[SwaggerTags.PAYMENT_METHODS],
    ),
    retrieve=extend_schema(
        summary="Get payment method details",
        description="Get detailed information about a specific payment method.",
        responses={
            200: PaymentMethodSerializer,
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=[SwaggerTags.PAYMENT_METHODS],
    ),
    update=extend_schema(
        summary="Update payment method",
        description="Update payment method details like name or default status.",
        responses={
            200: PaymentMethodSerializer,
            400: OpenApiResponse(description="Invalid payment method data"),
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=[SwaggerTags.PAYMENT_METHODS],
    ),
    destroy=extend_schema(
        summary="Delete payment method",
        description="Delete a payment method from the user's account.",
        responses={
            204: OpenApiResponse(description="Payment method deleted successfully"),
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=[SwaggerTags.PAYMENT_METHODS],
    ),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ## Payment Method Management

    Manage saved payment methods including credit cards, digital wallets, and bank accounts.

    ### 💳 Features
    - **Save Payment Methods**: Securely store payment method details
    - **Multiple Methods**: Support for various payment types (cards, wallets, etc.)
    - **Default Methods**: Set preferred payment method
    - **Method Status**: Activate/deactivate payment methods
    - **Expiry Tracking**: Monitor card expiration dates

    ### 🔐 Security
    - Users can only access their own payment methods
    - Sensitive data is tokenized and encrypted
    - PCI DSS compliant storage
    """

    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, IsUserOwnerOrReadOnly]

    def get_queryset(self):
        """Return payment methods for the current user."""
        # Avoid evaluating with AnonymousUser during schema generation
        if getattr(self, "swagger_fake_view", False):  # drf_yasg schema generation
            return PaymentMethod.objects.none()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return PaymentMethod.objects.none()
        return PaymentMethod.objects.filter(user=user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return PaymentMethodCreateSerializer
        return self.serializer_class

    @extend_schema(
        summary="Set as default payment method",
        description="Set this payment method as the user's default payment method.",
        responses={
            200: OpenApiResponse(
                response=PaymentMethodSerializer,
                description="Payment method set as default",
            ),
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=[SwaggerTags.PAYMENT_METHODS],
    )
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """Set payment method as default."""
        payment_method = self.get_object()

        # Remove default from other payment methods
        PaymentMethod.objects.filter(user=request.user, is_default=True).update(
            is_default=False
        )

        # Set this one as default
        payment_method.is_default = True
        payment_method.save()

        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List user transactions",
        description="Get a list of the current user's payment transactions with pagination and filtering.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                description="Filter by transaction status",
                enum=[
                    "pending",
                    "processing",
                    "succeeded",
                    "failed",
                    "cancelled",
                    "refunded",
                ],
            ),
            OpenApiParameter(
                name="transaction_type",
                type=str,
                description="Filter by transaction type",
                enum=["payment", "refund", "partial_refund", "chargeback"],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=TransactionSerializer(many=True),
                description="List of user transactions",
                examples=[
                    OpenApiExample(
                        "Transactions",
                        value=[
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "user_email": "user@example.com",
                                "payment_method_name": "Personal Visa Card",
                                "provider_name": "Stripe",
                                "transaction_type": "payment",
                                "status": "succeeded",
                                "amount": "99.99",
                                "currency": "USD",
                                "provider_fee": "3.29",
                                "description": "Product purchase",
                                "reference": "ORDER-001",
                                "processed_at": "2025-08-09T10:05:00Z",
                                "failed_at": None,
                                "error_message": "",
                                "is_refundable": True,
                                "created_at": "2025-08-09T10:00:00Z",
                                "updated_at": "2025-08-09T10:05:00Z",
                            }
                        ],
                    )
                ],
            )
        },
        tags=[SwaggerTags.TRANSACTIONS],
    ),
    create=extend_schema(
        summary="Create new transaction",
        description="Create a new payment transaction using a saved payment method.",
        request=TransactionCreateSerializer,
        responses={
            201: TransactionSerializer,
            400: OpenApiResponse(description="Invalid transaction data"),
        },
        examples=[
            OpenApiExample(
                "Create Transaction",
                value={
                    "payment_method": 1,
                    "provider": 1,
                    "amount": "99.99",
                    "currency": "USD",
                    "description": "Product purchase",
                    "reference": "ORDER-001",
                    "metadata": {"order_id": 123},
                },
            )
        ],
        tags=[SwaggerTags.TRANSACTIONS],
    ),
    retrieve=extend_schema(
        summary="Get transaction details",
        description="Get detailed information about a specific transaction.",
        responses={
            200: TransactionSerializer,
            404: OpenApiResponse(description="Transaction not found"),
        },
        tags=[SwaggerTags.TRANSACTIONS],
    ),
)
class TransactionViewSet(viewsets.ModelViewSet):
    """
    ## Payment Transaction Management

    View transaction history and process new payments.

    ### 💰 Features
    - **Transaction History**: View all payment transactions
    - **Transaction Details**: Get detailed information about specific payments
    - **Create Payments**: Process new payments using saved methods
    - **Status Tracking**: Monitor payment processing status
    - **Filtering**: Filter by status, type, date range
    - **Refund Support**: Handle refunds and partial refunds

    ### 📊 Transaction Types
    - **Payment**: Regular purchase transactions
    - **Refund**: Full transaction refunds
    - **Partial Refund**: Partial amount refunds
    - **Chargeback**: Disputed transaction handling

    ### 🔐 Security
    - Users can only access their own transactions
    - Secure payment processing
    - Complete audit trail
    """

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsUserOwnerOrReadOnly]
    http_method_names = ["get", "post", "options", "head"]

    def get_queryset(self):
        """Return transactions for the current user with optional filtering."""
        # Avoid evaluating with AnonymousUser during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Transaction.objects.none()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Transaction.objects.none()
        queryset = Transaction.objects.filter(user=user)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        type_filter = self.request.query_params.get("transaction_type")
        if type_filter:
            queryset = queryset.filter(transaction_type=type_filter)

        return queryset.select_related("payment_method", "provider")

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return TransactionCreateSerializer
        return self.serializer_class

    @extend_schema(
        summary="Initiate payment (Chapa)",
        description=(
            "Initiate a payment using the configured provider (defaults to Chapa).\n\n"
            "You can pass an amount/currency directly or a cart_id to derive totals."
        ),
        request=PaymentInitiationSerializer,
        responses={
            200: OpenApiResponse(
                response=PaymentInitiationResponseSerializer,
                description="Payment initialized; checkout URL included when applicable",
            ),
            400: OpenApiResponse(description="Invalid initiation request"),
        },
        tags=[SwaggerTags.TRANSACTIONS],
    )
    @action(detail=False, methods=["post"], url_path="initiate")
    def initiate_payment(self, request):
        """Create a Transaction and initialize payment with the provider (Chapa)."""
        serializer = PaymentInitiationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        amount = serializer.validated_data["amount"]
        currency = serializer.validated_data.get("currency", "ETB")
        description = serializer.validated_data.get("description", "")
        reference = serializer.validated_data.get("reference", "")
        metadata = serializer.validated_data.get("metadata", {})

        # Create a pending transaction record
        transaction_obj = Transaction.objects.create(
            user=request.user,
            provider=provider,
            transaction_type=Transaction.TransactionType.PAYMENT,
            status=Transaction.Status.PENDING,
            amount=amount,
            currency=currency,
            description=description,
            reference=reference,
            metadata=metadata,
            provider_transaction_id=f"txn_{request.user.id}_{timezone.now().timestamp()}",
        )

        # Initialize payment with provider (Chapa)
        payment_service = get_payment_service_from_provider(provider)
        user = request.user
        result = payment_service.initialize_payment(
            amount=amount,
            currency=currency,
            email=user.email,
            first_name=getattr(user, "first_name", "") or "Customer",
            last_name=getattr(user, "last_name", "") or "User",
            phone_number=getattr(user, "phone_number", ""),
            tx_ref=str(transaction_obj.id),
            callback_url=request.build_absolute_uri("/api/v1/payments/webhooks/chapa/"),
            return_url=request.build_absolute_uri(
                f"/api/v1/payments/transactions/{transaction_obj.id}/"
            ),
            description=description,
            metadata=metadata,
        )

        if result.success:
            transaction_obj.status = Transaction.Status.PROCESSING
            transaction_obj.provider_transaction_id = (
                result.provider_transaction_id
                or transaction_obj.provider_transaction_id
            )
            transaction_obj.metadata.update(
                {
                    "checkout_url": result.checkout_url,
                    "provider_response": result.raw_response,
                }
            )
            transaction_obj.save()
            return Response(
                {
                    "transaction_id": str(transaction_obj.id),
                    "status": transaction_obj.status,
                    "checkout_url": result.checkout_url,
                    "provider": provider.provider_type,
                    "message": result.message,
                }
            )
        else:
            transaction_obj.mark_as_failed(result.message)
            return Response(
                {"error": result.message, "error_code": result.error_code},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Verify payment (Chapa)",
        description="Verify a payment by transaction ID (tx_ref) and update its status accordingly.",
        request=PaymentVerificationRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=TransactionSerializer,
                description="Verification result with updated transaction",
            ),
            404: OpenApiResponse(description="Transaction not found"),
        },
        tags=[SwaggerTags.TRANSACTIONS],
    )
    @action(detail=False, methods=["post"], url_path="verify")
    def verify_payment(self, request):
        """Verify payment status from provider (Chapa) and persist updates."""
        serializer = PaymentVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx_ref = str(serializer.validated_data["tx_ref"])  # UUID to str

        try:
            transaction_obj = Transaction.objects.get(id=tx_ref, user=request.user)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND
            )

        payment_service = get_payment_service_from_provider(transaction_obj.provider)
        result = payment_service.verify_payment(tx_ref)

        if result.verified:
            transaction_obj.status = Transaction.Status.SUCCEEDED
            transaction_obj.provider_fee = result.provider_fee
            transaction_obj.metadata.update(
                {
                    "verification_result": result.raw_response,
                }
            )
            transaction_obj.save()
        else:
            # Keep existing status if already succeeded; otherwise mark failed with message
            if transaction_obj.status != Transaction.Status.SUCCEEDED:
                transaction_obj.mark_as_failed(result.message or "Verification failed")
            transaction_obj.metadata.update(
                {
                    "verification_result": result.raw_response,
                }
            )
            transaction_obj.save()

        return Response(TransactionSerializer(transaction_obj).data)

    @extend_schema(
        summary="Process transaction payment",
        description="Process the payment for a pending transaction through the payment provider.",
        responses={
            200: OpenApiResponse(
                response=TransactionSerializer,
                description="Transaction processed successfully",
            ),
            400: OpenApiResponse(description="Transaction cannot be processed"),
            404: OpenApiResponse(description="Transaction not found"),
        },
        tags=[SwaggerTags.TRANSACTIONS],
    )
    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Process a pending transaction."""
        transaction_obj = self.get_object()

        if transaction_obj.status != Transaction.Status.PENDING:
            return Response(
                {"error": "Transaction is not in pending status"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get payment service for the provider
            payment_service = get_payment_service_from_provider(
                transaction_obj.provider
            )

            # Initialize payment with the provider
            user = transaction_obj.user
            result = payment_service.initialize_payment(
                amount=transaction_obj.amount,
                currency=transaction_obj.currency,
                email=user.email,
                first_name=user.first_name or "Customer",
                last_name=user.last_name or "User",
                phone_number=getattr(user, "phone_number", ""),
                tx_ref=str(transaction_obj.id),
                callback_url=request.build_absolute_uri(
                    f"/api/v1/payments/webhooks/chapa/"
                ),
                return_url=request.build_absolute_uri(
                    f"/api/v1/payments/transactions/{transaction_obj.id}/"
                ),
                description=transaction_obj.description,
                metadata=transaction_obj.metadata,
            )

            if result.success:
                # Update transaction with provider details
                transaction_obj.provider_transaction_id = result.provider_transaction_id
                transaction_obj.status = Transaction.Status.PROCESSING
                transaction_obj.metadata.update(
                    {
                        "checkout_url": result.checkout_url,
                        "provider_response": result.raw_response,
                    }
                )
                transaction_obj.save()

                serializer = self.get_serializer(transaction_obj)
                response_data = serializer.data
                response_data["checkout_url"] = result.checkout_url

                return Response(response_data)
            else:
                # Mark transaction as failed
                transaction_obj.mark_as_failed(result.message)
                return Response(
                    {"error": result.message, "error_code": result.error_code},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            # Mark transaction as failed and log error
            transaction_obj.mark_as_failed(f"Payment processing error: {str(e)}")
            return Response(
                {"error": "Payment processing failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Refund transaction",
        description="Process a full or partial refund for a successful transaction.",
        request=RefundTransactionSerializer,
        responses={
            201: OpenApiResponse(
                response=TransactionSerializer,
                description="Refund transaction created",
            ),
            400: OpenApiResponse(description="Transaction cannot be refunded"),
            404: OpenApiResponse(description="Transaction not found"),
        },
        examples=[
            OpenApiExample(
                "Full Refund",
                value={"reason": "Customer requested refund"},
            ),
            OpenApiExample(
                "Partial Refund",
                value={"amount": "50.00", "reason": "Partial product return"},
            ),
        ],
        tags=[SwaggerTags.TRANSACTIONS],
    )
    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Process a refund for a transaction."""
        transaction_obj = self.get_object()

        serializer = RefundTransactionSerializer(
            data=request.data, context={"transaction": transaction_obj}
        )
        serializer.is_valid(raise_exception=True)

        refund_amount = (
            serializer.validated_data.get("amount") or transaction_obj.amount
        )
        reason = serializer.validated_data.get("reason", "")

        # Create refund transaction
        refund_transaction = Transaction.objects.create(
            user=transaction_obj.user,
            payment_method=transaction_obj.payment_method,
            provider=transaction_obj.provider,
            transaction_type=(
                Transaction.TransactionType.REFUND
                if refund_amount == transaction_obj.amount
                else Transaction.TransactionType.PARTIAL_REFUND
            ),
            status=Transaction.Status.SUCCEEDED,
            amount=refund_amount,
            currency=transaction_obj.currency,
            description=f"Refund for transaction {transaction_obj.id}",
            reference=f"REFUND-{transaction_obj.reference}",
            parent_transaction=transaction_obj,
            metadata={"reason": reason},
            processed_at=timezone.now(),
            provider_transaction_id=f"refund_{transaction_obj.provider_transaction_id}",
        )

        # Update original transaction status if fully refunded
        if refund_amount == transaction_obj.amount:
            transaction_obj.status = Transaction.Status.REFUNDED
            transaction_obj.save()
        elif refund_amount < transaction_obj.amount:
            transaction_obj.status = Transaction.Status.PARTIALLY_REFUNDED
            transaction_obj.save()

        refund_serializer = self.get_serializer(refund_transaction)
        return Response(refund_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        summary="List user carts",
        description="Get a list of the current user's shopping carts.",
        responses={
            200: OpenApiResponse(
                response=CartSerializer(many=True),
                description="List of user carts",
            )
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    create=extend_schema(
        summary="Create new cart",
        description="Create a new shopping cart for the current user. If an active cart exists, it will be returned instead.",
        request=CartCreateSerializer,
        responses={
            201: CartSerializer,
            200: OpenApiResponse(
                response=CartSerializer,
                description="Existing active cart returned",
            ),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    retrieve=extend_schema(
        summary="Get cart details",
        description="Get detailed information about a specific shopping cart including all items.",
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    update=extend_schema(
        summary="Update cart",
        description="Update cart information like notes or currency.",
        responses={
            200: CartSerializer,
            400: OpenApiResponse(description="Invalid cart data"),
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    destroy=extend_schema(
        summary="Delete cart",
        description="Delete a shopping cart and all its items.",
        responses={
            204: OpenApiResponse(description="Cart deleted successfully"),
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
)
class CartViewSet(viewsets.ModelViewSet):
    """
    ## Shopping Cart Management

    Create and manage shopping carts with comprehensive item handling.

    ### 🛒 Core Features
    - **Create Cart**: Get or create user's active shopping cart
    - **View Cart**: See cart details with all items and totals
    - **Update Cart**: Modify cart settings like currency and notes
    - **Delete Cart**: Remove cart and all its items

    ### 🛍️ Item Management
    - **Add Items**: Add products and variants to cart
    - **Update Quantities**: Modify item quantities
    - **Remove Items**: Delete specific items from cart
    - **Clear Cart**: Remove all items at once

    ### 💰 Price Calculation
    - **Subtotal**: Sum of all item prices
    - **Tax Calculation**: Automatic tax computation
    - **Shipping Costs**: Shipping fee calculation
    - **Discounts**: Apply promotional discounts
    - **Total**: Final cart total with all fees

    ### 🔐 Security
    - Users can only access their own carts
    - Stock validation on item addition
    - Inventory tracking and updates
    """

    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsUserOwnerOrReadOnly]

    def get_queryset(self):
        """Return carts for the current user."""
        # Avoid evaluating with AnonymousUser during schema generation
        if getattr(self, "swagger_fake_view", False):
            return Cart.objects.none()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return Cart.objects.none()
        return Cart.objects.filter(user=user).prefetch_related(
            "items__product", "items__variant"
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return CartCreateSerializer
        elif self.action == "summary":
            return CartSummarySerializer
        return self.serializer_class

    @extend_schema(
        summary="Get current active cart",
        description="Get the user's current active shopping cart or create one if it doesn't exist.",
        responses={
            200: CartSerializer,
            201: OpenApiResponse(
                response=CartSerializer,
                description="New cart created",
            ),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    )
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get or create the user's current active cart."""
        cart, created = Cart.objects.get_or_create(
            user=request.user,
            status=Cart.Status.ACTIVE,
            defaults={"currency": "USD"},
        )

        serializer = self.get_serializer(cart)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @extend_schema(
        summary="Add item to cart",
        description="Add a product or product variant to the shopping cart.",
        request=AddToCartSerializer,
        responses={
            200: OpenApiResponse(
                response=CartSerializer,
                description="Item added to cart",
            ),
            400: OpenApiResponse(description="Invalid item data"),
        },
        examples=[
            OpenApiExample(
                "Add Product to Cart",
                value={
                    "product_id": 1,
                    "quantity": 2,
                    "notes": "Gift wrapping required",
                },
            ),
            OpenApiExample(
                "Add Product Variant to Cart",
                value={
                    "product_id": 1,
                    "variant_id": 5,
                    "quantity": 1,
                    "custom_attributes": {"size": "Large", "color": "Blue"},
                },
            ),
        ],
        tags=[SwaggerTags.SHOPPING_CART],
    )
    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        """Add an item to the cart."""
        cart = self.get_object()

        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data["product"]
        variant = serializer.validated_data.get("variant")
        quantity = serializer.validated_data["quantity"]
        custom_attributes = serializer.validated_data.get("custom_attributes", {})
        notes = serializer.validated_data.get("notes", "")

        # Check if item already exists in cart
        existing_item = cart.items.filter(product=product, variant=variant).first()

        if existing_item:
            # Update existing item quantity
            existing_item.quantity += quantity
            existing_item.custom_attributes.update(custom_attributes)
            if notes:
                existing_item.notes = notes
            existing_item.save()
        else:
            # Create new cart item
            unit_price = variant.price if variant else product.price
            CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price,
                custom_attributes=custom_attributes,
                notes=notes,
            )

        cart_serializer = self.get_serializer(cart)
        return Response(cart_serializer.data)

    @extend_schema(
        summary="Clear cart",
        description="Remove all items from the shopping cart.",
        responses={
            200: OpenApiResponse(
                response=CartSerializer,
                description="Cart cleared successfully",
            ),
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    )
    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        """Clear all items from the cart."""
        cart = self.get_object()
        cart.clear()

        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @extend_schema(
        summary="Get cart summary",
        description="Get a summary of the cart with totals and item count.",
        responses={
            200: CartSummarySerializer,
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    )
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get cart summary with totals."""
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List cart items",
        description="Get a list of items in a specific cart.",
        responses={
            200: OpenApiResponse(
                response=CartItemSerializer(many=True),
                description="List of cart items",
            )
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    create=extend_schema(
        summary="Add item to cart",
        description="Add a new item to the specified cart.",
        request=CartItemCreateSerializer,
        responses={
            201: CartItemSerializer,
            400: OpenApiResponse(description="Invalid item data"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    retrieve=extend_schema(
        summary="Get cart item details",
        description="Get detailed information about a specific cart item.",
        responses={
            200: CartItemSerializer,
            404: OpenApiResponse(description="Cart item not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    update=extend_schema(
        summary="Update cart item",
        description="Update cart item quantity, attributes, or notes.",
        request=UpdateCartItemSerializer,
        responses={
            200: CartItemSerializer,
            400: OpenApiResponse(description="Invalid item data"),
            404: OpenApiResponse(description="Cart item not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
    destroy=extend_schema(
        summary="Remove item from cart",
        description="Remove an item from the shopping cart.",
        responses={
            204: OpenApiResponse(description="Item removed successfully"),
            404: OpenApiResponse(description="Cart item not found"),
        },
        tags=[SwaggerTags.SHOPPING_CART],
    ),
)
class CartItemViewSet(viewsets.ModelViewSet):
    """
    ## Cart Item Management

    Manage individual items within shopping carts with detailed control.

    ### 🛍️ Item Operations
    - **Add Items**: Add new products or variants to cart
    - **View Items**: Get detailed information about cart items
    - **Update Items**: Modify quantity, attributes, or notes
    - **Remove Items**: Delete specific items from cart

    ### 📦 Product Support
    - **Simple Products**: Add basic products to cart
    - **Product Variants**: Support for size, color, and custom attributes
    - **Custom Attributes**: Store additional item specifications
    - **Item Notes**: Add special instructions or notes

    ### 💰 Pricing Features
    - **Unit Price**: Individual item pricing
    - **Quantity**: Item quantity management
    - **Total Price**: Calculated item total (quantity × unit price)
    - **Stock Validation**: Ensure sufficient inventory

    ### 🔐 Security
    - Users can only manage items in their own carts
    - Inventory validation and stock checking
    - Price validation against current product pricing
    """

    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return cart items for the current user's carts."""
        # Avoid evaluating with AnonymousUser during schema generation
        if getattr(self, "swagger_fake_view", False):
            return CartItem.objects.none()
        user = getattr(self.request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return CartItem.objects.none()
        cart_id = self.kwargs.get("cart_pk")
        if cart_id:
            # When accessed through nested route
            return CartItem.objects.filter(
                cart_id=cart_id, cart__user=user
            ).select_related("product", "variant")
        else:
            # When accessed directly
            return CartItem.objects.filter(cart__user=user).select_related(
                "product", "variant", "cart"
            )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return CartItemCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateCartItemSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create cart item in the specified cart."""
        cart_id = self.kwargs.get("cart_pk")
        if cart_id:
            cart = get_object_or_404(Cart, id=cart_id, user=self.request.user)
            serializer.save(cart=cart)
        else:
            # If no cart specified, use or create current active cart
            cart, _ = Cart.objects.get_or_create(
                user=self.request.user,
                status=Cart.Status.ACTIVE,
                defaults={"currency": "USD"},
            )
            serializer.save(cart=cart)

    def perform_update(self, serializer):
        """Update cart item with validation."""
        cart_item = self.get_object()

        # Validate stock availability for new quantity
        new_quantity = serializer.validated_data.get("quantity", cart_item.quantity)

        if cart_item.variant:
            if cart_item.variant.stock_quantity < new_quantity:
                raise serializers.ValidationError(
                    "Not enough stock available for variant."
                )
        else:
            if (
                cart_item.product.track_inventory
                and cart_item.product.stock_quantity < new_quantity
            ):
                raise serializers.ValidationError(
                    "Not enough stock available for product."
                )

        serializer.save()
