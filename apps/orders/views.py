"""
Order Views.

API views for order management.
"""

from django.db.models import Q
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.core.capabilities import require_capability

from .models import Order, OrderItem, OrderNote, OrderStatus
from .serializers import (
    CheckoutSerializer,
    OrderActionSerializer,
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderNoteSerializer,
    PaymentRecordSerializer,
)
from .services import CheckoutService, InvalidOrderStateError, OrderError, OrderService


@extend_schema_view(
    list=extend_schema(
        summary="List Orders",
        description="List orders for the current user (or all orders for staff).",
        tags=["Orders"],
    ),
    retrieve=extend_schema(
        summary="Get Order Details",
        description="Get detailed information about a specific order.",
        tags=["Orders"],
    ),
    create=extend_schema(
        summary="Create Order",
        description="Create a new order directly (without cart).",
        tags=["Orders"],
    ),
)
@require_capability("orders")
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order management.
    
    Provides CRUD operations plus order-specific actions like
    place, cancel, refund, and fulfill.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get orders based on user role."""
        user = self.request.user
        queryset = Order.objects.select_related("customer").prefetch_related(
            "items", "status_history", "notes"
        )
        
        # Staff sees all orders, customers see only their own
        if user.is_staff:
            return queryset
        return queryset.filter(customer=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return OrderListSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        return Response(
            OrderDetailSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
    
    @extend_schema(
        summary="Place Order",
        description="Place a draft order (confirm and submit for payment).",
        request=None,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def place(self, request, pk=None):
        """Place/confirm a draft order."""
        order = self.get_object()
        
        try:
            order = OrderService.place_order(
                order,
                changed_by=request.user,
            )
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except InvalidOrderStateError as e:
            return Response(
                {"error": "invalid_state", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Cancel Order",
        description="Cancel an order.",
        request=OrderActionSerializer,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel an order."""
        order = self.get_object()
        serializer = OrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            order = OrderService.cancel_order(
                order,
                reason=serializer.validated_data.get("reason", ""),
                changed_by=request.user,
            )
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except InvalidOrderStateError as e:
            return Response(
                {"error": "invalid_state", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Refund Order",
        description="Process a refund for an order.",
        request=OrderActionSerializer,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Refund an order (staff only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "permission_denied", "message": "Staff only"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        order = self.get_object()
        serializer = OrderActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data.get("amount")
        if not amount:
            return Response(
                {"error": "validation_error", "message": "Amount is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            order = OrderService.refund_order(
                order,
                amount=amount,
                reason=serializer.validated_data.get("reason", ""),
                changed_by=request.user,
            )
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except (InvalidOrderStateError, OrderError) as e:
            return Response(
                {"error": "refund_failed", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Record Payment",
        description="Record a payment against an order (typically called by payment webhook).",
        request=PaymentRecordSerializer,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def record_payment(self, request, pk=None):
        """Record payment against order (staff/system only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "permission_denied", "message": "Staff only"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        order = self.get_object()
        serializer = PaymentRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            order = OrderService.record_payment(
                order,
                amount=serializer.validated_data["amount"],
                transaction_id=serializer.validated_data.get("transaction_id"),
                changed_by=request.user,
                metadata=serializer.validated_data.get("metadata"),
            )
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except OrderError as e:
            return Response(
                {"error": "payment_failed", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Mark Processing",
        description="Mark order as processing (preparing for fulfillment).",
        request=None,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def mark_processing(self, request, pk=None):
        """Mark order as processing (staff only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "permission_denied", "message": "Staff only"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        order = self.get_object()
        
        try:
            order = OrderService.mark_processing(order, changed_by=request.user)
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except InvalidOrderStateError as e:
            return Response(
                {"error": "invalid_state", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Complete Order",
        description="Mark order as completed.",
        request=None,
        responses={200: OrderDetailSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark order as completed (staff only)."""
        if not request.user.is_staff:
            return Response(
                {"error": "permission_denied", "message": "Staff only"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        order = self.get_object()
        
        try:
            order = OrderService.complete_order(order, changed_by=request.user)
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data
            )
        except InvalidOrderStateError as e:
            return Response(
                {"error": "invalid_state", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Add Note",
        description="Add a note to an order.",
        request=OrderNoteSerializer,
        responses={201: OrderNoteSerializer},
        tags=["Orders"],
    )
    @action(detail=True, methods=["post"])
    def add_note(self, request, pk=None):
        """Add a note to an order."""
        order = self.get_object()
        
        serializer = OrderNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Customers can only add customer-visible notes
        is_customer_visible = serializer.validated_data.get("is_customer_visible", False)
        if not request.user.is_staff:
            is_customer_visible = True
        
        note = OrderNote.objects.create(
            order=order,
            author=request.user,
            content=serializer.validated_data["content"],
            is_customer_visible=is_customer_visible,
        )
        
        return Response(
            OrderNoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    create=extend_schema(
        summary="Checkout",
        description="Create an order from the current user's cart.",
        tags=["Checkout"],
    ),
)
@require_capability("orders")
class CheckoutViewSet(viewsets.ViewSet):
    """
    ViewSet for checkout operations.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Checkout from Cart",
        description="""
        Create an order from the user's current cart.
        
        This endpoint:
        1. Validates the cart (stock, pricing)
        2. Creates an order with all cart items
        3. Returns the order ready for payment
        """,
        request=CheckoutSerializer,
        responses={201: OrderDetailSerializer},
        tags=["Checkout"],
    )
    def create(self, request):
        """Checkout from cart."""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get user's active cart
        from apps.payments.models import Cart
        
        cart_id = serializer.validated_data.get("cart_id")
        if cart_id:
            cart = Cart.objects.filter(id=cart_id, user=request.user).first()
        else:
            cart = Cart.objects.filter(user=request.user).first()
        
        if not cart:
            return Response(
                {"error": "cart_not_found", "message": "No active cart found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Validate checkout
        is_valid, errors = CheckoutService.validate_checkout(cart)
        if not is_valid:
            return Response(
                {"error": "validation_failed", "messages": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Get IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")
        
        # Create order from cart
        try:
            order = CheckoutService.create_order_from_cart(
                cart=cart,
                customer=request.user,
                billing_address=serializer.validated_data.get("billing_address"),
                shipping_address=serializer.validated_data.get("shipping_address"),
                customer_notes=serializer.validated_data.get("customer_notes", ""),
                ip_address=ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            
            # Place the order
            order = OrderService.place_order(order, changed_by=request.user)
            
            # Optionally clear the cart
            cart.items.all().delete()
            
            return Response(
                OrderDetailSerializer(order, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        except OrderError as e:
            return Response(
                {"error": "checkout_failed", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @extend_schema(
        summary="Validate Checkout",
        description="Validate cart is ready for checkout without creating an order.",
        responses={200: {"type": "object"}},
        tags=["Checkout"],
    )
    @action(detail=False, methods=["post"])
    def validate(self, request):
        """Validate checkout without creating order."""
        from apps.payments.models import Cart
        
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return Response(
                {"valid": False, "errors": ["No active cart found"]},
                status=status.HTTP_200_OK,
            )
        
        is_valid, errors = CheckoutService.validate_checkout(cart)
        return Response({
            "valid": is_valid,
            "errors": errors,
            "cart_total": str(cart.total) if hasattr(cart, "total") else None,
        })
