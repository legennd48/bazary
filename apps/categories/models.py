"""
Category models for organizing products.
"""

from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class CategoryManager(models.Manager):
    """Custom manager for Category model."""

    def active(self):
        """Return only active categories."""
        return self.filter(is_active=True)

    def get_tree(self):
        """Return categories in a tree structure."""
        return self.filter(parent=None, is_active=True).prefetch_related(
            "subcategories"
        )


class Category(TimeStampedModel):
    """Product category model with hierarchy support."""

    name = models.CharField(
        max_length=100, unique=True, help_text="Category name (unique)"
    )
    slug = models.SlugField(
        max_length=100, unique=True, help_text="URL-friendly category identifier"
    )
    description = models.TextField(blank=True, help_text="Category description")
    image = models.ImageField(
        upload_to="categories/", null=True, blank=True, help_text="Category image"
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
        default=True, help_text="Whether category is active"
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Display order")

    objects = CategoryManager()

    class Meta:
        db_table = "categories"
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["parent"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["sort_order"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return full category path."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    @property
    def has_children(self):
        """Check if category has subcategories."""
        return self.subcategories.exists()

    def get_descendants(self):
        """Get all descendant categories."""
        descendants = []
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
