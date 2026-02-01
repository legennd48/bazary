"""
Order Domain Services.

Business logic for order management, separate from API layer.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    FulfillmentStatus,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    OrderType,
    PaymentStatus,
)


class OrderError(Exception):
    """Base exception for order operations."""
    pass


class InvalidOrderStateError(OrderError):
    """Raised when operation is invalid for current order state."""
    pass


class InsufficientStockError(OrderError):
    """Raised when product stock is insufficient."""
    pass


class OrderService:
    """
    Service class for order operations.
    
    Centralizes business logic for:
    - Order creation and checkout
    - Status transitions
    - Payment recording
    - Fulfillment tracking
    - Cancellations and refunds
    """
    
    @classmethod
    @transaction.atomic
    def create_order(
        cls,
        customer=None,
        customer_email: str = "",
        items: List[Dict[str, Any]] = None,
        billing_address: Dict = None,
        shipping_address: Dict = None,
        currency: str = "USD",
        source: str = "web",
        customer_notes: str = "",
        metadata: Dict = None,
        ip_address: str = None,
        user_agent: str = "",
    ) -> Order:
        """
        Create a new order.
        
        Args:
            customer: User instance (optional for guest checkout)
            customer_email: Customer email address
            items: List of item dicts with product/service details
            billing_address: Billing address dict
            shipping_address: Shipping address dict
            currency: Currency code
            source: Order source (web, mobile, api, admin)
            customer_notes: Notes from customer
            metadata: Additional metadata
            ip_address: IP address of order placement
            user_agent: User agent string
            
        Returns:
            Created Order instance
        """
        # Determine order type based on items
        order_type = cls._determine_order_type(items or [])
        
        order = Order.objects.create(
            customer=customer,
            customer_email=customer_email or (customer.email if customer else ""),
            customer_phone=customer.phone_number if customer else "",
            order_type=order_type,
            status=OrderStatus.DRAFT,
            currency=currency,
            billing_address=billing_address or {},
            shipping_address=shipping_address or {},
            customer_notes=customer_notes,
            metadata=metadata or {},
            source=source,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Add items
        if items:
            for item_data in items:
                cls.add_item(order, **item_data)
        
        # Calculate totals
        order.calculate_totals()
        order.save()
        
        return order
    
    @classmethod
    def _determine_order_type(cls, items: List[Dict]) -> str:
        """Determine order type based on items."""
        types = set()
        for item in items:
            item_type = item.get("item_type", "product")
            if item_type == "product":
                types.add("product")
            elif item_type == "service":
                types.add("service")
            elif item_type == "booking":
                types.add("booking")
        
        if len(types) > 1:
            return OrderType.MIXED
        elif "service" in types:
            return OrderType.SERVICE
        elif "booking" in types:
            return OrderType.BOOKING
        return OrderType.PRODUCT
    
    @classmethod
    def add_item(
        cls,
        order: Order,
        name: str,
        unit_price: Decimal,
        quantity: int = 1,
        item_type: str = "product",
        product_id: str = None,
        variant_id: str = None,
        service_id: str = None,
        booking_id: str = None,
        sku: str = "",
        description: str = "",
        variant_options: Dict = None,
        requires_shipping: bool = True,
        is_digital: bool = False,
        metadata: Dict = None,
    ) -> OrderItem:
        """Add an item to an order."""
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError(
                f"Cannot add items to order in {order.status} status"
            )
        
        item = OrderItem.objects.create(
            order=order,
            item_type=item_type,
            product_id=product_id,
            variant_id=variant_id,
            service_id=service_id,
            booking_id=booking_id,
            name=name,
            sku=sku,
            description=description,
            variant_options=variant_options or {},
            unit_price=Decimal(str(unit_price)),
            quantity=quantity,
            requires_shipping=requires_shipping,
            is_digital=is_digital,
            metadata=metadata or {},
        )
        
        return item
    
    @classmethod
    @transaction.atomic
    def place_order(
        cls,
        order: Order,
        changed_by=None,
    ) -> Order:
        """
        Place an order (convert from draft to pending).
        
        This is the "checkout" action - validates and confirms the order.
        """
        if order.status != OrderStatus.DRAFT:
            raise InvalidOrderStateError(
                f"Can only place orders in DRAFT status, got {order.status}"
            )
        
        if not order.items.exists():
            raise OrderError("Cannot place order with no items")
        
        # Recalculate totals
        order.calculate_totals()
        
        # Transition to pending
        cls._transition_status(
            order,
            OrderStatus.PENDING,
            changed_by=changed_by,
            reason="Order placed",
        )
        
        order.placed_at = timezone.now()
        order.save()
        
        return order
    
    @classmethod
    @transaction.atomic
    def record_payment(
        cls,
        order: Order,
        amount: Decimal,
        transaction_id: str = None,
        changed_by=None,
        metadata: Dict = None,
    ) -> Order:
        """
        Record a payment against an order.
        
        Updates payment status and order status accordingly.
        """
        amount = Decimal(str(amount))
        order.amount_paid += amount
        
        # Update payment status
        if order.amount_paid >= order.total:
            order.payment_status = PaymentStatus.PAID
            order.paid_at = timezone.now()
            
            # Transition order to PAID status
            cls._transition_status(
                order,
                OrderStatus.PAID,
                changed_by=changed_by,
                reason=f"Payment received: {amount}",
                metadata={"transaction_id": transaction_id, **(metadata or {})},
            )
        elif order.amount_paid > Decimal("0"):
            order.payment_status = PaymentStatus.PARTIALLY_PAID
        
        order.save()
        return order
    
    @classmethod
    @transaction.atomic
    def mark_processing(cls, order: Order, changed_by=None) -> Order:
        """Mark order as processing (preparing for fulfillment)."""
        if order.status not in {OrderStatus.PAID, OrderStatus.PENDING}:
            raise InvalidOrderStateError(
                f"Cannot mark {order.status} order as processing"
            )
        
        cls._transition_status(
            order,
            OrderStatus.PROCESSING,
            changed_by=changed_by,
            reason="Order processing started",
        )
        order.save()
        return order
    
    @classmethod
    @transaction.atomic
    def fulfill_item(
        cls,
        order: Order,
        item: OrderItem,
        quantity: int,
        changed_by=None,
    ) -> OrderItem:
        """Fulfill (partially or fully) an order item."""
        remaining = item.quantity - item.quantity_fulfilled
        if quantity > remaining:
            raise OrderError(
                f"Cannot fulfill {quantity} items, only {remaining} remaining"
            )
        
        item.quantity_fulfilled += quantity
        
        if item.quantity_fulfilled >= item.quantity:
            item.fulfillment_status = FulfillmentStatus.FULFILLED
        else:
            item.fulfillment_status = FulfillmentStatus.PARTIALLY_FULFILLED
        
        item.save()
        
        # Update order fulfillment status
        cls._update_order_fulfillment_status(order, changed_by)
        
        return item
    
    @classmethod
    def _update_order_fulfillment_status(cls, order: Order, changed_by=None) -> None:
        """Update order's overall fulfillment status based on items."""
        items = order.items.all()
        all_fulfilled = all(item.is_fulfilled for item in items)
        any_fulfilled = any(item.quantity_fulfilled > 0 for item in items)
        
        if all_fulfilled:
            order.fulfillment_status = FulfillmentStatus.FULFILLED
            order.fulfilled_at = timezone.now()
            
            # Transition to fulfilled
            cls._transition_status(
                order,
                OrderStatus.FULFILLED,
                changed_by=changed_by,
                reason="All items fulfilled",
            )
        elif any_fulfilled:
            order.fulfillment_status = FulfillmentStatus.PARTIALLY_FULFILLED
            order.status = OrderStatus.PARTIALLY_FULFILLED
        
        order.save()
    
    @classmethod
    @transaction.atomic
    def cancel_order(
        cls,
        order: Order,
        reason: str = "",
        changed_by=None,
    ) -> Order:
        """Cancel an order."""
        if not order.can_cancel:
            raise InvalidOrderStateError(
                f"Cannot cancel order in {order.status} status"
            )
        
        cls._transition_status(
            order,
            OrderStatus.CANCELLED,
            changed_by=changed_by,
            reason=reason or "Order cancelled",
        )
        
        order.cancelled_at = timezone.now()
        order.save()
        
        return order
    
    @classmethod
    @transaction.atomic
    def refund_order(
        cls,
        order: Order,
        amount: Decimal,
        reason: str = "",
        changed_by=None,
    ) -> Order:
        """Process a refund for an order."""
        if not order.can_refund:
            raise InvalidOrderStateError("Cannot refund this order")
        
        amount = Decimal(str(amount))
        max_refundable = order.amount_paid - order.amount_refunded
        
        if amount > max_refundable:
            raise OrderError(
                f"Cannot refund {amount}, maximum refundable is {max_refundable}"
            )
        
        order.amount_refunded += amount
        
        if order.amount_refunded >= order.amount_paid:
            order.payment_status = PaymentStatus.REFUNDED
            cls._transition_status(
                order,
                OrderStatus.REFUNDED,
                changed_by=changed_by,
                reason=reason or f"Full refund: {amount}",
            )
        else:
            order.payment_status = PaymentStatus.PARTIALLY_REFUNDED
            cls._transition_status(
                order,
                OrderStatus.PARTIALLY_REFUNDED,
                changed_by=changed_by,
                reason=reason or f"Partial refund: {amount}",
            )
        
        order.save()
        return order
    
    @classmethod
    @transaction.atomic
    def complete_order(cls, order: Order, changed_by=None) -> Order:
        """Mark order as completed."""
        if order.status not in {
            OrderStatus.FULFILLED,
            OrderStatus.DELIVERED,
            OrderStatus.PAID,  # For digital/service orders
        }:
            raise InvalidOrderStateError(
                f"Cannot complete order in {order.status} status"
            )
        
        cls._transition_status(
            order,
            OrderStatus.COMPLETED,
            changed_by=changed_by,
            reason="Order completed",
        )
        
        order.completed_at = timezone.now()
        order.save()
        
        return order
    
    @classmethod
    def _transition_status(
        cls,
        order: Order,
        new_status: str,
        changed_by=None,
        reason: str = "",
        metadata: Dict = None,
    ) -> OrderStatusHistory:
        """
        Transition order to a new status with history tracking.
        """
        old_status = order.status
        order.status = new_status
        
        history = OrderStatusHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            reason=reason,
            metadata=metadata or {},
        )
        
        return history


class CheckoutService:
    """
    Service for handling checkout workflow.
    
    Converts cart to order and initiates payment.
    """
    
    @classmethod
    @transaction.atomic
    def create_order_from_cart(
        cls,
        cart,  # Cart model instance
        customer=None,
        billing_address: Dict = None,
        shipping_address: Dict = None,
        customer_notes: str = "",
        ip_address: str = None,
        user_agent: str = "",
    ) -> Order:
        """
        Create an order from a shopping cart.
        
        Args:
            cart: Cart instance with items
            customer: User (optional)
            billing_address: Billing address dict
            shipping_address: Shipping address dict
            customer_notes: Notes from customer
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Created Order
        """
        # Build items from cart
        items = []
        for cart_item in cart.items.all():
            item_data = {
                "name": cart_item.product.name,
                "unit_price": cart_item.unit_price,
                "quantity": cart_item.quantity,
                "item_type": "product",
                "product_id": str(cart_item.product.id) if cart_item.product else None,
                "sku": cart_item.product.sku if cart_item.product else "",
                "requires_shipping": not cart_item.product.is_digital if cart_item.product else True,
                "is_digital": cart_item.product.is_digital if cart_item.product else False,
            }
            
            # Add variant info if present
            if cart_item.variant:
                item_data["variant_id"] = str(cart_item.variant.id)
                item_data["sku"] = cart_item.variant.sku or item_data["sku"]
                # Capture variant options
                item_data["variant_options"] = cls._get_variant_options(cart_item.variant)
            
            items.append(item_data)
        
        # Create order
        order = OrderService.create_order(
            customer=customer or cart.user,
            customer_email=customer.email if customer else (cart.user.email if cart.user else ""),
            items=items,
            billing_address=billing_address,
            shipping_address=shipping_address,
            currency=getattr(cart, "currency", "USD"),
            source="web",
            customer_notes=customer_notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return order
    
    @classmethod
    def _get_variant_options(cls, variant) -> Dict:
        """Extract variant option values as a dict."""
        options = {}
        try:
            for option_value in variant.option_values.all():
                options[option_value.option.name] = option_value.value
        except Exception:
            pass
        return options
    
    @classmethod
    def validate_checkout(cls, cart) -> Tuple[bool, List[str]]:
        """
        Validate cart is ready for checkout.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not cart.items.exists():
            errors.append("Cart is empty")
            return False, errors
        
        # Check stock for each item
        for item in cart.items.all():
            if item.product and item.product.track_inventory:
                available = item.product.stock_quantity
                if item.variant and hasattr(item.variant, "stock_quantity"):
                    available = item.variant.stock_quantity
                
                if item.quantity > available:
                    errors.append(
                        f"Insufficient stock for {item.product.name}: "
                        f"requested {item.quantity}, available {available}"
                    )
        
        return len(errors) == 0, errors
