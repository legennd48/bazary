"""
Service Models.

Comprehensive service offering management for service-based businesses.
"""

import uuid
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class ServiceCategory(TimeStampedModel):
    """
    Category for organizing services.
    
    Separate from product categories to allow different taxonomies.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Category name",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier",
    )
    description = models.TextField(
        blank=True,
        help_text="Category description",
    )
    image = models.ImageField(
        upload_to="service_categories/",
        null=True,
        blank=True,
        help_text="Category image",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        help_text="Parent category for hierarchy",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether category is active",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order",
    )
    
    class Meta:
        db_table = "service_categories"
        verbose_name_plural = "Service categories"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PricingType(models.TextChoices):
    """How service is priced."""
    FIXED = "fixed", "Fixed Price"
    HOURLY = "hourly", "Per Hour"
    DAILY = "daily", "Per Day"
    CUSTOM = "custom", "Custom Quote"
    FREE = "free", "Free"


class ServiceStatus(models.TextChoices):
    """Service availability status."""
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Service(TimeStampedModel):
    """
    Core service model.
    
    Represents a service offering with pricing, duration, and provider info.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="Service name",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly identifier",
    )
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief service summary",
    )
    description = models.TextField(
        help_text="Detailed service description",
    )
    
    # Categorization
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
        help_text="Service category",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Service tags for filtering",
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.DRAFT,
        db_index=True,
        help_text="Service status",
    )
    
    # Pricing
    pricing_type = models.CharField(
        max_length=20,
        choices=PricingType.choices,
        default=PricingType.FIXED,
        help_text="How service is priced",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Service price (interpretation depends on pricing_type)",
    )
    compare_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price (for discounts)",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code (ISO 4217)",
    )
    
    # Duration
    duration_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Service duration in minutes",
    )
    buffer_before_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Buffer time before service",
    )
    buffer_after_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Buffer time after service",
    )
    
    # Capacity
    max_attendees = models.PositiveIntegerField(
        default=1,
        help_text="Maximum attendees per session (1 for 1-on-1)",
    )
    min_attendees = models.PositiveIntegerField(
        default=1,
        help_text="Minimum attendees to confirm booking",
    )
    
    # Booking requirements
    requires_booking = models.BooleanField(
        default=True,
        help_text="Whether service requires booking",
    )
    advance_booking_days = models.PositiveIntegerField(
        default=30,
        help_text="How many days in advance can book",
    )
    min_notice_hours = models.PositiveIntegerField(
        default=24,
        help_text="Minimum notice hours for booking",
    )
    
    # Cancellation policy
    cancellation_policy = models.TextField(
        blank=True,
        help_text="Cancellation policy text",
    )
    free_cancellation_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours before service for free cancellation",
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to="services/",
        null=True,
        blank=True,
        help_text="Featured service image",
    )
    
    # SEO
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta title",
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description",
    )
    
    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_services",
    )
    
    class Meta:
        db_table = "services"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["pricing_type"]),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def total_duration_minutes(self) -> int:
        """Total duration including buffers."""
        return (
            self.buffer_before_minutes
            + self.duration_minutes
            + self.buffer_after_minutes
        )
    
    @property
    def is_active(self) -> bool:
        """Check if service is active."""
        return self.status == ServiceStatus.ACTIVE
    
    @property
    def discount_percentage(self) -> int:
        """Calculate discount percentage."""
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0


class ServiceImage(TimeStampedModel):
    """Additional images for a service."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to="services/gallery/",
        help_text="Service image",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alternative text for accessibility",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order",
    )
    
    class Meta:
        db_table = "service_images"
        ordering = ["sort_order", "created_at"]
    
    def __str__(self):
        return f"{self.service.name} - Image"


class ServiceProvider(TimeStampedModel):
    """
    Links services to staff members who can provide them.
    
    A provider is a user (staff) who can perform services.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_providers",
        help_text="Staff user",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="providers",
        help_text="Service they provide",
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary provider",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether provider is active for this service",
    )
    
    # Provider-specific settings
    custom_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Custom price for this provider (overrides service price)",
    )
    custom_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Custom duration for this provider (overrides service duration)",
    )
    
    # Bio and display
    bio = models.TextField(
        blank=True,
        help_text="Provider bio for this service",
    )
    
    class Meta:
        db_table = "service_providers"
        unique_together = ["user", "service"]
        ordering = ["-is_primary", "user__first_name"]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.service.name}"
    
    @property
    def effective_price(self) -> Decimal:
        """Get effective price (custom or service default)."""
        return self.custom_price if self.custom_price else self.service.price
    
    @property
    def effective_duration(self) -> int:
        """Get effective duration (custom or service default)."""
        return self.custom_duration if self.custom_duration else self.service.duration_minutes


class ServiceAddon(TimeStampedModel):
    """
    Optional add-ons for services.
    
    E.g., for a massage service: "Add aromatherapy +$20"
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="addons",
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Add-on name",
    )
    description = models.TextField(
        blank=True,
        help_text="Add-on description",
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Additional price",
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Additional duration in minutes",
    )
    is_active = models.BooleanField(
        default=True,
    )
    
    class Meta:
        db_table = "service_addons"
        ordering = ["name"]
    
    def __str__(self):
        return f"{self.service.name} - {self.name}"
