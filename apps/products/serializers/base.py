"""
Base product serializers.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.categories.serializers import CategorySerializer
from apps.products.models import Product, ProductImage, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "created_at"]
        read_only_fields = ["id", "slug", "created_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "is_primary", "sort_order", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view (minimal fields)."""

    category = CategorySerializer(read_only=True)
    primary_image = ProductImageSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    has_variants = serializers.BooleanField(read_only=True)
    variant_price_range = serializers.JSONField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "price",
            "compare_price",
            "category",
            "primary_image",
            "tags",
            "is_featured",
            "is_in_stock",
            "discount_percentage",
            "has_variants",
            "variant_price_range",
            "created_at",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view (all fields)."""

    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    has_variants = serializers.BooleanField(read_only=True)
    variant_price_range = serializers.JSONField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "short_description",
            "sku",
            "price",
            "compare_price",
            "category",
            "tags",
            "track_inventory",
            "stock_quantity",
            "low_stock_threshold",
            "is_active",
            "is_featured",
            "is_digital",
            "meta_title",
            "meta_description",
            "images",
            "is_in_stock",
            "is_low_stock",
            "discount_percentage",
            "has_variants",
            "variant_price_range",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "sku",
            "created_by",
            "created_at",
            "updated_at",
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "short_description",
            "price",
            "compare_price",
            "cost_price",
            "category",
            "tags",
            "track_inventory",
            "stock_quantity",
            "low_stock_threshold",
            "is_active",
            "is_featured",
            "is_digital",
            "meta_title",
            "meta_description",
        ]

    def validate_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

    def validate_compare_price(self, value):
        """Validate compare price is greater than price if provided."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Compare price must be greater than 0")
        return value

    def validate(self, data):
        """Cross-field validation."""
        price = data.get("price")
        compare_price = data.get("compare_price")

        if price and compare_price and compare_price <= price:
            raise serializers.ValidationError(
                {"compare_price": "Compare price must be greater than price"}
            )

        return data


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for product search results."""

    category = CategorySerializer(read_only=True)
    primary_image = ProductImageSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    has_variants = serializers.BooleanField(read_only=True)
    variant_price_range = serializers.JSONField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "price",
            "compare_price",
            "category",
            "primary_image",
            "tags",
            "is_featured",
            "is_in_stock",
            "discount_percentage",
            "has_variants",
            "variant_price_range",
        ]
