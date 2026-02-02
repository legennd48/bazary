"""
Coupon and Discount Service.

Provides coupon validation, application, and discount calculation.
Supports:
- Percentage and fixed amount discounts
- Minimum order requirements
- Usage limits (total and per-user)
- Date-based validity
- Category and product restrictions
- First-time customer discounts
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional
import logging
import secrets
import string

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

logger = logging.getLogger(__name__)


# ============================================================================
# Coupon Models
# ============================================================================

class Coupon(TimeStampedModel):
    """
    Coupon/discount code model.
    """
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage Off"
        FIXED_AMOUNT = "fixed_amount", "Fixed Amount Off"
        FREE_SHIPPING = "free_shipping", "Free Shipping"
        BUY_X_GET_Y = "buy_x_get_y", "Buy X Get Y"
    
    class AppliesTo(models.TextChoices):
        ALL = "all", "All Products"
        SPECIFIC_PRODUCTS = "specific_products", "Specific Products"
        SPECIFIC_CATEGORIES = "specific_categories", "Specific Categories"
        SPECIFIC_COLLECTIONS = "specific_collections", "Specific Collections"
    
    # Basic Info
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Coupon code (case-insensitive)",
    )
    name = models.CharField(
        max_length=200,
        help_text="Internal name for the coupon",
    )
    description = models.TextField(
        blank=True,
        help_text="Description shown to customers",
    )
    
    # Discount Configuration
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        help_text="Type of discount",
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Discount value (percentage or fixed amount)",
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount amount (for percentage discounts)",
    )
    
    # Applicability
    applies_to = models.CharField(
        max_length=30,
        choices=AppliesTo.choices,
        default=AppliesTo.ALL,
        help_text="What the discount applies to",
    )
    product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of product IDs for specific product discounts",
    )
    category_slugs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of category slugs for specific category discounts",
    )
    
    # Requirements
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Minimum order amount to use coupon",
    )
    minimum_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Minimum number of items to use coupon",
    )
    first_order_only = models.BooleanField(
        default=False,
        help_text="Only valid for customer's first order",
    )
    
    # Usage Limits
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum total uses (null = unlimited)",
    )
    usage_limit_per_customer = models.PositiveIntegerField(
        default=1,
        help_text="Maximum uses per customer",
    )
    times_used = models.PositiveIntegerField(
        default=0,
        help_text="Number of times coupon has been used",
    )
    
    # Validity Period
    valid_from = models.DateTimeField(
        help_text="When coupon becomes valid",
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When coupon expires (null = no expiry)",
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether coupon is currently active",
    )
    
    # Stacking rules
    combinable = models.BooleanField(
        default=False,
        help_text="Whether coupon can be combined with other coupons",
    )
    
    class Meta:
        db_table = "coupons"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code", "is_active"]),
            models.Index(fields=["valid_from", "valid_until"]),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = timezone.now()
        
        if not self.is_active:
            return False
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        
        return True
    
    @property
    def discount_display(self) -> str:
        """Human-readable discount description."""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            text = f"{self.discount_value}% off"
            if self.max_discount_amount:
                text += f" (up to ${self.max_discount_amount})"
            return text
        elif self.discount_type == self.DiscountType.FIXED_AMOUNT:
            return f"${self.discount_value} off"
        elif self.discount_type == self.DiscountType.FREE_SHIPPING:
            return "Free shipping"
        return str(self.discount_value)


class CouponUsage(TimeStampedModel):
    """
    Tracks coupon usage by customers.
    """
    
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="usages",
        help_text="Coupon that was used",
    )
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="coupon_usages",
        help_text="User who used the coupon",
    )
    order_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Order where coupon was applied",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Actual discount amount applied",
    )
    
    class Meta:
        db_table = "coupon_usages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["coupon", "user"]),
        ]
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"


# ============================================================================
# Discount Calculation Data Classes
# ============================================================================

@dataclass
class DiscountLine:
    """Individual discount line in a calculation."""
    coupon_code: str
    coupon_name: str
    discount_type: str
    discount_amount: Decimal
    applies_to: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "coupon_code": self.coupon_code,
            "coupon_name": self.coupon_name,
            "discount_type": self.discount_type,
            "discount_amount": str(self.discount_amount),
            "applies_to": self.applies_to,
        }


@dataclass
class DiscountCalculation:
    """Result of discount calculation."""
    subtotal: Decimal
    total_discount: Decimal
    discounted_subtotal: Decimal
    free_shipping: bool
    discount_lines: List[DiscountLine]
    applied_coupons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subtotal": str(self.subtotal),
            "total_discount": str(self.total_discount),
            "discounted_subtotal": str(self.discounted_subtotal),
            "free_shipping": self.free_shipping,
            "discount_lines": [line.to_dict() for line in self.discount_lines],
            "applied_coupons": self.applied_coupons,
        }


# ============================================================================
# Exceptions
# ============================================================================

class CouponError(Exception):
    """Base exception for coupon operations."""
    pass


class InvalidCouponError(CouponError):
    """Raised when coupon is invalid."""
    def __init__(self, message: str, code: str = "invalid"):
        self.message = message
        self.code = code
        super().__init__(message)


# ============================================================================
# Coupon Service
# ============================================================================

class CouponService:
    """
    Service for coupon validation and application.
    
    Handles:
    - Coupon code validation
    - Discount calculation
    - Usage tracking
    - Multiple coupon stacking (when allowed)
    """
    
    @classmethod
    def validate_coupon(
        cls,
        code: str,
        user=None,
        subtotal: Decimal = Decimal("0.00"),
        item_count: int = 0,
        category_slugs: List[str] = None,
        product_ids: List[str] = None,
    ) -> Coupon:
        """
        Validate a coupon code.
        
        Args:
            code: Coupon code to validate
            user: User attempting to use coupon
            subtotal: Cart subtotal
            item_count: Number of items in cart
            category_slugs: Categories of items in cart
            product_ids: Product IDs in cart
            
        Returns:
            Valid Coupon instance
            
        Raises:
            InvalidCouponError: If coupon is invalid
        """
        code = code.strip().upper()
        
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            raise InvalidCouponError("Invalid coupon code", "not_found")
        
        now = timezone.now()
        
        # Check basic validity
        if not coupon.is_active:
            raise InvalidCouponError("This coupon is no longer active", "inactive")
        
        if now < coupon.valid_from:
            raise InvalidCouponError("This coupon is not yet valid", "not_started")
        
        if coupon.valid_until and now > coupon.valid_until:
            raise InvalidCouponError("This coupon has expired", "expired")
        
        # Check usage limits
        if coupon.usage_limit and coupon.times_used >= coupon.usage_limit:
            raise InvalidCouponError("This coupon has reached its usage limit", "usage_limit")
        
        # Check per-customer usage
        if user and coupon.usage_limit_per_customer:
            user_usage = CouponUsage.objects.filter(
                coupon=coupon,
                user=user,
            ).count()
            if user_usage >= coupon.usage_limit_per_customer:
                raise InvalidCouponError(
                    "You have already used this coupon the maximum number of times",
                    "user_limit"
                )
        
        # Check first order requirement
        if coupon.first_order_only and user:
            from apps.orders.models import Order, OrderStatus
            has_orders = Order.objects.filter(
                customer=user,
                status__in=[
                    OrderStatus.PAID,
                    OrderStatus.PROCESSING,
                    OrderStatus.SHIPPED,
                    OrderStatus.DELIVERED,
                    OrderStatus.COMPLETED,
                ]
            ).exists()
            if has_orders:
                raise InvalidCouponError(
                    "This coupon is only valid for first-time customers",
                    "not_first_order"
                )
        
        # Check minimum requirements
        if subtotal < coupon.minimum_order_amount:
            raise InvalidCouponError(
                f"Minimum order of ${coupon.minimum_order_amount} required",
                "minimum_order"
            )
        
        if item_count < coupon.minimum_quantity:
            raise InvalidCouponError(
                f"Minimum of {coupon.minimum_quantity} items required",
                "minimum_quantity"
            )
        
        # Check product/category applicability
        if coupon.applies_to == Coupon.AppliesTo.SPECIFIC_PRODUCTS:
            if not product_ids or not any(
                str(pid) in coupon.product_ids for pid in product_ids
            ):
                raise InvalidCouponError(
                    "This coupon is not valid for the items in your cart",
                    "products_not_applicable"
                )
        
        if coupon.applies_to == Coupon.AppliesTo.SPECIFIC_CATEGORIES:
            if not category_slugs or not any(
                cat in coupon.category_slugs for cat in category_slugs
            ):
                raise InvalidCouponError(
                    "This coupon is not valid for the items in your cart",
                    "categories_not_applicable"
                )
        
        return coupon
    
    @classmethod
    def calculate_discount(
        cls,
        subtotal: Decimal,
        coupon_codes: List[str],
        user=None,
        item_count: int = 0,
        category_slugs: List[str] = None,
        product_ids: List[str] = None,
    ) -> DiscountCalculation:
        """
        Calculate total discount from applied coupons.
        
        Args:
            subtotal: Cart subtotal
            coupon_codes: List of coupon codes to apply
            user: User making the purchase
            item_count: Number of items
            category_slugs: Categories of items
            product_ids: Product IDs
            
        Returns:
            DiscountCalculation with breakdown
        """
        subtotal = Decimal(str(subtotal))
        discount_lines = []
        total_discount = Decimal("0.00")
        free_shipping = False
        applied_coupons = []
        
        # Track if we've applied a non-combinable coupon
        has_non_combinable = False
        
        for code in coupon_codes:
            try:
                coupon = cls.validate_coupon(
                    code=code,
                    user=user,
                    subtotal=subtotal,
                    item_count=item_count,
                    category_slugs=category_slugs,
                    product_ids=product_ids,
                )
            except InvalidCouponError:
                continue  # Skip invalid coupons
            
            # Check stacking rules
            if has_non_combinable:
                continue  # Can't add more coupons after a non-combinable one
            if not coupon.combinable and applied_coupons:
                continue  # Non-combinable coupon can't be added if others already applied
            
            # Calculate discount
            discount_amount = Decimal("0.00")
            
            if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
                discount_amount = (subtotal * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"))
                if coupon.max_discount_amount:
                    discount_amount = min(discount_amount, coupon.max_discount_amount)
            
            elif coupon.discount_type == Coupon.DiscountType.FIXED_AMOUNT:
                discount_amount = min(coupon.discount_value, subtotal)
            
            elif coupon.discount_type == Coupon.DiscountType.FREE_SHIPPING:
                free_shipping = True
            
            if discount_amount > Decimal("0.00") or coupon.discount_type == Coupon.DiscountType.FREE_SHIPPING:
                discount_lines.append(DiscountLine(
                    coupon_code=coupon.code,
                    coupon_name=coupon.name,
                    discount_type=coupon.discount_type,
                    discount_amount=discount_amount,
                    applies_to=coupon.applies_to,
                ))
                total_discount += discount_amount
                applied_coupons.append(coupon.code)
                
                if not coupon.combinable:
                    has_non_combinable = True
        
        # Ensure discount doesn't exceed subtotal
        total_discount = min(total_discount, subtotal)
        
        return DiscountCalculation(
            subtotal=subtotal,
            total_discount=total_discount,
            discounted_subtotal=subtotal - total_discount,
            free_shipping=free_shipping,
            discount_lines=discount_lines,
            applied_coupons=applied_coupons,
        )
    
    @classmethod
    def apply_coupon(
        cls,
        coupon: Coupon,
        user,
        order_id: str,
        discount_amount: Decimal,
    ) -> CouponUsage:
        """
        Record coupon usage after successful order.
        
        Args:
            coupon: Coupon that was used
            user: User who used it
            order_id: Order ID
            discount_amount: Actual discount applied
            
        Returns:
            CouponUsage record
        """
        usage = CouponUsage.objects.create(
            coupon=coupon,
            user=user,
            order_id=order_id,
            discount_amount=discount_amount,
        )
        
        # Increment usage counter
        coupon.times_used += 1
        coupon.save(update_fields=["times_used"])
        
        return usage
    
    @classmethod
    def generate_coupon_code(cls, length: int = 8, prefix: str = "") -> str:
        """
        Generate a unique coupon code.
        
        Args:
            length: Length of random part
            prefix: Optional prefix
            
        Returns:
            Unique coupon code
        """
        chars = string.ascii_uppercase + string.digits
        while True:
            random_part = ''.join(secrets.choice(chars) for _ in range(length))
            code = f"{prefix}{random_part}" if prefix else random_part
            if not Coupon.objects.filter(code=code).exists():
                return code
    
    @classmethod
    def create_coupon(
        cls,
        code: str = None,
        name: str = "",
        discount_type: str = Coupon.DiscountType.PERCENTAGE,
        discount_value: Decimal = Decimal("10.00"),
        valid_days: int = 30,
        usage_limit: int = None,
        minimum_order: Decimal = None,
        first_order_only: bool = False,
        **kwargs,
    ) -> Coupon:
        """
        Create a new coupon with sensible defaults.
        
        Args:
            code: Coupon code (auto-generated if not provided)
            name: Internal name
            discount_type: Type of discount
            discount_value: Discount amount
            valid_days: Number of days coupon is valid
            usage_limit: Maximum uses
            minimum_order: Minimum order amount
            first_order_only: First order restriction
            **kwargs: Additional coupon fields
            
        Returns:
            Created Coupon
        """
        if not code:
            code = cls.generate_coupon_code()
        
        now = timezone.now()
        
        return Coupon.objects.create(
            code=code.upper(),
            name=name or f"Coupon {code}",
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=now,
            valid_until=now + timezone.timedelta(days=valid_days) if valid_days else None,
            usage_limit=usage_limit,
            minimum_order_amount=minimum_order or Decimal("0.00"),
            first_order_only=first_order_only,
            is_active=True,
            **kwargs,
        )
    
    @classmethod
    def get_active_coupons(cls, public_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get list of active coupons.
        
        Args:
            public_only: Only return coupons meant for public display
            
        Returns:
            List of coupon info dicts
        """
        now = timezone.now()
        
        coupons = Coupon.objects.filter(
            is_active=True,
            valid_from__lte=now,
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
        ).filter(
            models.Q(usage_limit__isnull=True) | models.Q(times_used__lt=models.F("usage_limit"))
        )
        
        return [
            {
                "code": c.code,
                "name": c.name,
                "description": c.description,
                "discount_display": c.discount_display,
                "minimum_order": str(c.minimum_order_amount),
                "valid_until": c.valid_until.isoformat() if c.valid_until else None,
                "first_order_only": c.first_order_only,
            }
            for c in coupons
        ]
