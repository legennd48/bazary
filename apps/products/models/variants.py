"""
Product variant models for handling product options like size, color, etc.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class VariantOption(TimeStampedModel):
    """
    Variant option types (e.g., Color, Size, Material).
    """

    name = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Option name (e.g., 'Color', 'Size')"
    )
    display_name = models.CharField(
        max_length=100, 
        help_text="Display name for frontend"
    )
    display_type = models.CharField(
        max_length=20,
        choices=[
            ('dropdown', 'Dropdown'),
            ('color', 'Color Picker'),
            ('button', 'Button Selection'),
            ('radio', 'Radio Button'),
        ],
        default='dropdown',
        help_text="How this option should be displayed"
    )
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this option is required for the product"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of options"
    )

    class Meta:
        db_table = "variant_options"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.display_name


class VariantOptionValue(TimeStampedModel):
    """
    Values for variant options (e.g., Red, Blue for Color; S, M, L for Size).
    """

    option = models.ForeignKey(
        VariantOption,
        on_delete=models.CASCADE,
        related_name="values",
        help_text="The option this value belongs to"
    )
    value = models.CharField(
        max_length=100,
        help_text="The actual value (e.g., 'Red', 'Small')"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Display name for frontend"
    )
    color_code = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        help_text="Hex color code for color options"
    )
    image = models.ImageField(
        upload_to="variant_values/",
        blank=True,
        null=True,
        help_text="Optional image for this value"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of values"
    )

    class Meta:
        db_table = "variant_option_values"
        ordering = ["sort_order", "value"]
        unique_together = ["option", "value"]

    def __str__(self):
        return f"{self.option.name}: {self.display_name}"


class ProductVariant(TimeStampedModel):
    """
    Specific product variants with their own pricing and inventory.
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="variants",
        help_text="The base product this variant belongs to"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique SKU for this variant"
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Variant-specific price (overrides product price if set)"
    )
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price for this variant"
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price for this variant"
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Stock quantity for this variant"
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Low stock warning threshold for this variant"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this variant is available"
    )
    
    # Physical attributes
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in grams"
    )
    dimensions_length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Length in cm"
    )
    dimensions_width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Width in cm"
    )
    dimensions_height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Height in cm"
    )

    class Meta:
        db_table = "product_variants"
        ordering = ["sku"]
        indexes = [
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["stock_quantity"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.sku}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate SKU."""
        if not self.sku:
            # Generate SKU based on product SKU + variant count
            base_sku = self.product.sku
            variant_count = ProductVariant.objects.filter(product=self.product).count()
            self.sku = f"{base_sku}-V{variant_count + 1:03d}"
        super().save(*args, **kwargs)

    @property
    def effective_price(self):
        """Get the effective price (variant price or product price)."""
        return self.price if self.price is not None else self.product.price

    @property
    def is_in_stock(self):
        """Check if this variant is in stock."""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if this variant is low in stock."""
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        """Calculate discount percentage for this variant."""
        compare_price = self.compare_price or self.product.compare_price
        effective_price = self.effective_price
        
        if compare_price and compare_price > effective_price:
            return int(((compare_price - effective_price) / compare_price) * 100)
        return 0


class ProductVariantOption(TimeStampedModel):
    """
    Links a product variant to its option values (e.g., Red + Large).
    """

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="option_values"
    )
    option = models.ForeignKey(
        VariantOption,
        on_delete=models.CASCADE,
        help_text="The option type (e.g., Color, Size)"
    )
    value = models.ForeignKey(
        VariantOptionValue,
        on_delete=models.CASCADE,
        help_text="The selected value (e.g., Red, Large)"
    )

    class Meta:
        db_table = "product_variant_options"
        unique_together = ["variant", "option"]
        indexes = [
            models.Index(fields=["variant", "option"]),
        ]

    def __str__(self):
        return f"{self.variant.sku} - {self.option.name}: {self.value.display_name}"

    def clean(self):
        """Validate that the value belongs to the correct option."""
        if self.value.option != self.option:
            raise ValueError("Value must belong to the selected option")

    def save(self, *args, **kwargs):
        """Override save to validate data."""
        self.clean()
        super().save(*args, **kwargs)


class ProductVariantImage(TimeStampedModel):
    """
    Images specific to product variants.
    """

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(
        upload_to="variant_images/",
        help_text="Variant-specific image"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary image for the variant"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )

    class Meta:
        db_table = "product_variant_images"
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["variant", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.variant.sku} - Image {self.id}"

    def save(self, *args, **kwargs):
        """Override save to auto-generate alt text."""
        if not self.alt_text:
            self.alt_text = f"{self.variant.product.name} {self.variant.sku} image"
        super().save(*args, **kwargs)
