"""
Base product models for the e-commerce system.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.authentication.models import User
from apps.categories.models import Category
from apps.core.models import TimeStampedModel


class ProductManager(models.Manager):
    """Custom manager for Product model."""

    def active(self):
        """Return only active products."""
        return self.filter(is_active=True)

    def in_stock(self):
        """Return products that are in stock."""
        return self.filter(
            models.Q(track_inventory=False) | models.Q(stock_quantity__gt=0)
        )

    def featured(self):
        """Return featured products."""
        return self.filter(is_featured=True, is_active=True)

    def by_category(self, category_slug):
        """Return products by category slug."""
        return self.filter(category__slug=category_slug, is_active=True)


class Tag(TimeStampedModel):
    """Tag model for product categorization."""

    name = models.CharField(max_length=50, unique=True, help_text="Tag name")
    slug = models.SlugField(
        max_length=50, unique=True, help_text="URL-friendly tag identifier"
    )
    color = models.CharField(
        max_length=7, default="#007bff", help_text="Tag color (hex code)"
    )

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    """Product model with comprehensive fields."""

    name = models.CharField(max_length=255, help_text="Product name")
    slug = models.SlugField(
        max_length=255, unique=True, help_text="URL-friendly product identifier"
    )
    description = models.TextField(help_text="Detailed product description")
    short_description = models.CharField(
        max_length=500, blank=True, help_text="Brief product summary"
    )
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Product price in USD",
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price (for discounts)",
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price (admin only)",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        help_text="Product category",
    )
    tags = models.ManyToManyField(
        Tag, blank=True, help_text="Product tags for filtering"
    )

    # Inventory
    track_inventory = models.BooleanField(
        default=True, help_text="Whether to track inventory"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0, help_text="Current stock quantity"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10, help_text="Low stock warning threshold"
    )

    # Status
    is_active = models.BooleanField(default=True, help_text="Whether product is active")
    is_featured = models.BooleanField(
        default=False, help_text="Whether product is featured"
    )
    is_digital = models.BooleanField(
        default=False, help_text="Whether product is digital"
    )

    # SEO
    meta_title = models.CharField(
        max_length=255, blank=True, help_text="SEO meta title"
    )
    meta_description = models.TextField(blank=True, help_text="SEO meta description")

    # Audit
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_products"
    )

    objects = ProductManager()

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["price"]),
            models.Index(fields=["created_at"]),
            # Composite indexes for filtering
            models.Index(fields=["category", "price"]),
            models.Index(fields=["is_active", "stock_quantity"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug and SKU."""
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            # Generate a simple SKU based on name
            base_sku = "".join([word[:3].upper() for word in self.name.split()[:3]])
            # Add a number to make it unique
            counter = 1
            sku = f"{base_sku}{counter:03d}"
            while Product.objects.filter(sku=sku).exists():
                counter += 1
                sku = f"{base_sku}{counter:03d}"
            self.sku = sku
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def primary_image(self):
        """Get the primary product image."""
        return self.images.filter(is_primary=True).first()

    @property
    def has_variants(self):
        """Check if product has variants."""
        return self.variants.exists()

    @property
    def available_variants(self):
        """Get active variants for this product."""
        return self.variants.filter(is_active=True)

    @property
    def variant_price_range(self):
        """Get price range for variants."""
        variants = self.available_variants
        if not variants.exists():
            return None

        prices = []
        for variant in variants:
            prices.append(variant.effective_price)

        if not prices:
            return None

        min_price = min(prices)
        max_price = max(prices)

        if min_price == max_price:
            return {"min": min_price, "max": max_price, "single": True}
        return {"min": min_price, "max": max_price, "single": False}


class ProductImage(TimeStampedModel):
    """Product image model for multiple images per product."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/", help_text="Product image")
    alt_text = models.CharField(
        max_length=255, blank=True, help_text="Alternative text for accessibility"
    )
    is_primary = models.BooleanField(
        default=False, help_text="Whether this is the primary image"
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")

    class Meta:
        db_table = "product_images"
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate alt text."""
        if not self.alt_text:
            self.alt_text = f"{self.product.name} image"
        super().save(*args, **kwargs)
