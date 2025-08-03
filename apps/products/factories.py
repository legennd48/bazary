"""
Factory classes for testing products app.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model

import factory
from factory import fuzzy

from apps.categories.models import Category

from .models import Product, ProductImage, Tag

User = get_user_model()


class CategoryFactory(factory.django.DjangoModelFactory):
    """Factory for Category model."""

    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=200)
    is_active = True


class TagFactory(factory.django.DjangoModelFactory):
    """Factory for Tag model."""

    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"Tag {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    color = factory.Faker("hex_color")


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for Product model."""

    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Product {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("text", max_nb_chars=500)
    short_description = factory.Faker("text", max_nb_chars=150)
    sku = factory.Sequence(lambda n: f"SKU{n:06d}")
    price = fuzzy.FuzzyDecimal(10.00, 1000.00, 2)
    compare_price = factory.LazyAttribute(
        lambda obj: obj.price + Decimal("10.00") if obj.price else None
    )
    cost_price = factory.LazyAttribute(
        lambda obj: obj.price * Decimal("0.7") if obj.price else None
    )
    category = factory.SubFactory(CategoryFactory)
    track_inventory = True
    stock_quantity = fuzzy.FuzzyInteger(0, 100)
    low_stock_threshold = 5
    is_active = True
    is_featured = False
    is_digital = False
    meta_title = factory.LazyAttribute(lambda obj: obj.name)
    meta_description = factory.LazyAttribute(lambda obj: obj.short_description)

    @factory.post_generation
    def created_by(self, create, extracted, **kwargs):
        """Set created_by to a user."""
        if not create:
            return

        if extracted:
            self.created_by = extracted
        else:
            # Create a user if one wasn't provided
            user = User.objects.create_user(
                username=f"user{self.id}",
                email=f"user{self.id}@example.com",
                password="testpass123",
            )
            self.created_by = user

        self.save()

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags to the product."""
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class ProductImageFactory(factory.django.DjangoModelFactory):
    """Factory for ProductImage model."""

    class Meta:
        model = ProductImage

    product = factory.SubFactory(ProductFactory)
    image = factory.django.ImageField(width=800, height=600, format="JPEG")
    alt_text = factory.Faker("sentence", nb_words=3)
    is_primary = False
    sort_order = factory.Sequence(lambda n: n)


class FeaturedProductFactory(ProductFactory):
    """Factory for featured products."""

    is_featured = True


class DigitalProductFactory(ProductFactory):
    """Factory for digital products."""

    is_digital = True
    track_inventory = False
    stock_quantity = 0


class OutOfStockProductFactory(ProductFactory):
    """Factory for out of stock products."""

    track_inventory = True
    stock_quantity = 0


class LowStockProductFactory(ProductFactory):
    """Factory for low stock products."""

    track_inventory = True
    stock_quantity = 3
    low_stock_threshold = 5
