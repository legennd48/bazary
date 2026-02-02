"""
Wishlist Models.

User wishlist/favorites functionality for products and services.
"""

import uuid
from django.db import models
from django.conf import settings

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Wishlist(TimeStampedModel):
    """
    User wishlist model.
    
    Each user has one default wishlist, but can create multiple named wishlists.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
        help_text="User who owns this wishlist",
    )
    name = models.CharField(
        max_length=100,
        default="My Wishlist",
        help_text="Wishlist name",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the user's default wishlist",
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this wishlist is publicly visible",
    )
    share_token = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Token for sharing private wishlists",
    )
    
    class Meta:
        db_table = "wishlists"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_wishlist_per_user",
            )
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def item_count(self) -> int:
        """Get number of items in wishlist."""
        return self.items.count()
    
    def save(self, *args, **kwargs):
        """Ensure only one default wishlist per user."""
        if self.is_default:
            Wishlist.objects.filter(
                user=self.user,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        
        # Generate share token if public
        if self.is_public and not self.share_token:
            import secrets
            self.share_token = secrets.token_urlsafe(32)
        
        super().save(*args, **kwargs)


class WishlistItem(TimeStampedModel):
    """
    Individual item in a wishlist.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    wishlist = models.ForeignKey(
        Wishlist,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent wishlist",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        help_text="Product in wishlist",
    )
    variant_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Specific variant (optional)",
    )
    notes = models.TextField(
        blank=True,
        help_text="User notes about this item",
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Priority/order within wishlist",
    )
    notify_on_sale = models.BooleanField(
        default=True,
        help_text="Notify user when item goes on sale",
    )
    notify_on_restock = models.BooleanField(
        default=True,
        help_text="Notify user when out-of-stock item is restocked",
    )
    
    class Meta:
        db_table = "wishlist_items"
        ordering = ["priority", "-created_at"]
        unique_together = ["wishlist", "product", "variant_id"]
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist.name}"
    
    @property
    def is_available(self) -> bool:
        """Check if item is currently available."""
        if not self.product.is_active:
            return False
        if self.product.track_inventory:
            return self.product.stock_quantity > 0
        return True
    
    @property
    def is_on_sale(self) -> bool:
        """Check if item is currently on sale."""
        return (
            self.product.compare_price is not None
            and self.product.compare_price > self.product.price
        )
