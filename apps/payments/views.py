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
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrReadOnly

from .models import Cart, CartItem, PaymentMethod, PaymentProvider, Transaction
from .serializers import (
    AddToCartSerializer,
    CartCreateSerializer,
    CartItemCreateSerializer,
    CartItemSerializer,
    CartSerializer,
    CartSummarySerializer,
    PaymentMethodCreateSerializer,
    PaymentMethodSerializer,
    PaymentProviderSerializer,
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
        tags=["Payment Providers"],
    ),
    retrieve=extend_schema(
        summary="Get payment provider details",
        description="Get detailed information about a specific payment provider.",
        responses={
            200: PaymentProviderSerializer,
            404: OpenApiResponse(description="Payment provider not found"),
        },
        tags=["Payment Providers"],
    ),
)
class PaymentProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payment provider management viewset.
    
    Provides read-only access to payment provider information.
    Only active providers are returned to users.
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
        tags=["Payment Methods"],
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
        tags=["Payment Methods"],
    ),
    retrieve=extend_schema(
        summary="Get payment method details",
        description="Get detailed information about a specific payment method.",
        responses={
            200: PaymentMethodSerializer,
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=["Payment Methods"],
    ),
    update=extend_schema(
        summary="Update payment method",
        description="Update payment method details like name or default status.",
        responses={
            200: PaymentMethodSerializer,
            400: OpenApiResponse(description="Invalid payment method data"),
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=["Payment Methods"],
    ),
    destroy=extend_schema(
        summary="Delete payment method",
        description="Delete a payment method from the user's account.",
        responses={
            204: OpenApiResponse(description="Payment method deleted successfully"),
            404: OpenApiResponse(description="Payment method not found"),
        },
        tags=["Payment Methods"],
    ),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    Payment method management viewset.
    
    Allows users to manage their saved payment methods including
    credit cards, digital wallets, and other payment options.
    """
    
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return payment methods for the current user."""
        return PaymentMethod.objects.filter(user=self.request.user)

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
        tags=["Payment Methods"],
    )
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """Set payment method as default."""
        payment_method = self.get_object()
        
        # Remove default from other payment methods
        PaymentMethod.objects.filter(
            user=request.user, is_default=True
        ).update(is_default=False)
        
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
                enum=["pending", "processing", "succeeded", "failed", "cancelled", "refunded"],
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
        tags=["Transactions"],
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
        tags=["Transactions"],
    ),
    retrieve=extend_schema(
        summary="Get transaction details",
        description="Get detailed information about a specific transaction.",
        responses={
            200: TransactionSerializer,
            404: OpenApiResponse(description="Transaction not found"),
        },
        tags=["Transactions"],
    ),
)
class TransactionViewSet(viewsets.ModelViewSet):
    """
    Payment transaction management viewset.
    
    Allows users to view their transaction history and create new transactions.
    Supports filtering by status and transaction type.
    """
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ["get", "post", "options", "head"]

    def get_queryset(self):
        """Return transactions for the current user with optional filtering."""
        queryset = Transaction.objects.filter(user=self.request.user)
        
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
        tags=["Transactions"],
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
            payment_service = get_payment_service_from_provider(transaction_obj.provider)
            
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
                callback_url=request.build_absolute_uri(f"/api/v1/payments/webhooks/chapa/"),
                return_url=request.build_absolute_uri(f"/api/v1/payments/transactions/{transaction_obj.id}/"),
                description=transaction_obj.description,
                metadata=transaction_obj.metadata,
            )
            
            if result.success:
                # Update transaction with provider details
                transaction_obj.provider_transaction_id = result.provider_transaction_id
                transaction_obj.status = Transaction.Status.PROCESSING
                transaction_obj.metadata.update({
                    "checkout_url": result.checkout_url,
                    "provider_response": result.raw_response,
                })
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
        tags=["Transactions"],
    )
    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Process a refund for a transaction."""
        transaction_obj = self.get_object()
        
        serializer = RefundTransactionSerializer(
            data=request.data, context={"transaction": transaction_obj}
        )
        serializer.is_valid(raise_exception=True)
        
        refund_amount = serializer.validated_data.get("amount") or transaction_obj.amount
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
        tags=["Shopping Cart"],
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
        tags=["Shopping Cart"],
    ),
    retrieve=extend_schema(
        summary="Get cart details",
        description="Get detailed information about a specific shopping cart including all items.",
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=["Shopping Cart"],
    ),
    update=extend_schema(
        summary="Update cart",
        description="Update cart information like notes or currency.",
        responses={
            200: CartSerializer,
            400: OpenApiResponse(description="Invalid cart data"),
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=["Shopping Cart"],
    ),
    destroy=extend_schema(
        summary="Delete cart",
        description="Delete a shopping cart and all its items.",
        responses={
            204: OpenApiResponse(description="Cart deleted successfully"),
            404: OpenApiResponse(description="Cart not found"),
        },
        tags=["Shopping Cart"],
    ),
)
class CartViewSet(viewsets.ModelViewSet):
    """
    Shopping cart management viewset.
    
    Allows users to create and manage their shopping carts.
    Supports adding/removing items and calculating totals.
    """
    
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Return carts for the current user."""
        return Cart.objects.filter(user=self.request.user).prefetch_related(
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
        tags=["Shopping Cart"],
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
        tags=["Shopping Cart"],
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
        existing_item = cart.items.filter(
            product=product, variant=variant
        ).first()
        
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
        tags=["Shopping Cart"],
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
        tags=["Shopping Cart"],
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
        tags=["Cart Items"],
    ),
    create=extend_schema(
        summary="Add item to cart",
        description="Add a new item to the specified cart.",
        request=CartItemCreateSerializer,
        responses={
            201: CartItemSerializer,
            400: OpenApiResponse(description="Invalid item data"),
        },
        tags=["Cart Items"],
    ),
    retrieve=extend_schema(
        summary="Get cart item details",
        description="Get detailed information about a specific cart item.",
        responses={
            200: CartItemSerializer,
            404: OpenApiResponse(description="Cart item not found"),
        },
        tags=["Cart Items"],
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
        tags=["Cart Items"],
    ),
    destroy=extend_schema(
        summary="Remove item from cart",
        description="Remove an item from the shopping cart.",
        responses={
            204: OpenApiResponse(description="Item removed successfully"),
            404: OpenApiResponse(description="Cart item not found"),
        },
        tags=["Cart Items"],
    ),
)
class CartItemViewSet(viewsets.ModelViewSet):
    """
    Cart item management viewset.
    
    Allows users to manage individual items within their shopping carts.
    Supports quantity updates and item removal.
    """
    
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return cart items for the current user's carts."""
        cart_id = self.kwargs.get("cart_pk")
        if cart_id:
            # When accessed through nested route
            return CartItem.objects.filter(
                cart_id=cart_id, cart__user=self.request.user
            ).select_related("product", "variant")
        else:
            # When accessed directly
            return CartItem.objects.filter(
                cart__user=self.request.user
            ).select_related("product", "variant", "cart")

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
            cart = get_object_or_404(
                Cart, id=cart_id, user=self.request.user
            )
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
