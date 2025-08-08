"""
Enhanced product serializers for advanced features.
"""

from rest_framework import serializers

from apps.products.models import Product, ProductImage
from apps.products.serializers.base import (
    ProductDetailSerializer,
    ProductListSerializer,
)
from apps.products.serializers.variants import ProductVariantListSerializer


class ProductImageUploadSerializer(serializers.Serializer):
    """Serializer for uploading product images."""

    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        help_text="List of images to upload",
    )

    def update(self, instance, validated_data):
        """Upload multiple images for a product."""
        images = validated_data.get("images", [])

        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=instance,
                image=image,
                sort_order=index,
                is_primary=(
                    index == 0 and not instance.images.filter(is_primary=True).exists()
                ),
            )

        return instance


class EnhancedProductListSerializer(ProductListSerializer):
    """Enhanced product list serializer with variants and advanced features."""

    variants = ProductVariantListSerializer(
        source="available_variants", many=True, read_only=True
    )
    variants_count = serializers.IntegerField(read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    image_count = serializers.IntegerField(read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "variants",
            "variants_count",
            "total_stock",
            "image_count",
        ]

    def to_representation(self, instance):
        """Add computed fields."""
        data = super().to_representation(instance)

        # Add computed fields
        data["variants_count"] = instance.variants.filter(is_active=True).count()
        data["total_stock"] = (
            sum(
                variant.stock_quantity
                for variant in instance.variants.filter(is_active=True)
            )
            if instance.has_variants
            else instance.stock_quantity
        )
        data["image_count"] = instance.images.count()

        return data


class EnhancedProductDetailSerializer(ProductDetailSerializer):
    """Enhanced product detail serializer with full variant and analytics data."""

    variants = ProductVariantListSerializer(
        source="available_variants", many=True, read_only=True
    )
    all_variants = ProductVariantListSerializer(
        source="variants", many=True, read_only=True
    )
    variants_count = serializers.IntegerField(read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    view_count = serializers.IntegerField(default=0, read_only=True)

    class Meta(ProductDetailSerializer.Meta):
        fields = ProductDetailSerializer.Meta.fields + [
            "variants",
            "all_variants",
            "variants_count",
            "total_stock",
            "view_count",
        ]

    def to_representation(self, instance):
        """Add computed fields and analytics."""
        data = super().to_representation(instance)

        # Add computed fields
        data["variants_count"] = instance.variants.count()
        data["total_stock"] = (
            sum(variant.stock_quantity for variant in instance.variants.all())
            if instance.has_variants
            else instance.stock_quantity
        )

        # Add analytics data (placeholder for future implementation)
        data["view_count"] = 0  # TODO: Implement view tracking

        return data


class ProductBulkOperationSerializer(serializers.Serializer):
    """Serializer for bulk product operations."""

    action = serializers.ChoiceField(
        choices=[
            ("activate", "Activate Products"),
            ("deactivate", "Deactivate Products"),
            ("update_price", "Update Prices"),
            ("update_stock", "Update Stock"),
            ("assign_category", "Assign Category"),
            ("add_tags", "Add Tags"),
            ("remove_tags", "Remove Tags"),
            ("delete", "Delete Products"),
        ],
        help_text="The bulk action to perform",
    )

    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of product IDs to apply the action to",
    )

    # Optional parameters for different actions
    price_adjustment = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Price adjustment amount (for update_price action)",
    )

    price_adjustment_type = serializers.ChoiceField(
        choices=[
            ("set", "Set Price"),
            ("increase", "Increase"),
            ("decrease", "Decrease"),
        ],
        required=False,
        default="set",
        help_text="Type of price adjustment",
    )

    stock_quantity = serializers.IntegerField(
        required=False, help_text="Stock quantity to set (for update_stock action)"
    )

    category_id = serializers.IntegerField(
        required=False, help_text="Category ID to assign (for assign_category action)"
    )

    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Tag IDs for tag operations",
    )

    def validate_product_ids(self, value):
        """Validate that all product IDs exist."""
        if not value:
            raise serializers.ValidationError("At least one product ID is required")

        existing_ids = set(
            Product.objects.filter(id__in=value).values_list("id", flat=True)
        )
        invalid_ids = set(value) - existing_ids

        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid product IDs: {', '.join(map(str, invalid_ids))}"
            )

        return value

    def validate(self, data):
        """Cross-field validation based on action."""
        action = data.get("action")

        if action == "update_price" and not data.get("price_adjustment"):
            raise serializers.ValidationError(
                {
                    "price_adjustment": (
                        "Price adjustment is required for update_price action"
                    )
                }
            )

        if action == "update_stock" and data.get("stock_quantity") is None:
            raise serializers.ValidationError(
                {"stock_quantity": "Stock quantity is required for update_stock action"}
            )

        if action == "assign_category" and not data.get("category_id"):
            raise serializers.ValidationError(
                {"category_id": "Category ID is required for assign_category action"}
            )

        if action in ["add_tags", "remove_tags"] and not data.get("tag_ids"):
            raise serializers.ValidationError(
                {"tag_ids": "Tag IDs are required for tag operations"}
            )

        return data


class ProductImportSerializer(serializers.Serializer):
    """Serializer for importing products from CSV/Excel."""

    file = serializers.FileField(help_text="CSV or Excel file containing product data")

    update_existing = serializers.BooleanField(
        default=False, help_text="Whether to update existing products with the same SKU"
    )

    validate_only = serializers.BooleanField(
        default=False, help_text="Only validate the data without importing"
    )

    def validate_file(self, value):
        """Validate file format."""
        allowed_extensions = [".csv", ".xlsx", ".xls"]
        file_extension = None

        if hasattr(value, "name"):
            file_extension = "." + value.name.split(".")[-1].lower()

        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File must be one of: {', '.join(allowed_extensions)}"
            )

        # Validate file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")

        return value


class ProductExportSerializer(serializers.Serializer):
    """Serializer for exporting products."""

    format = serializers.ChoiceField(
        choices=[("csv", "CSV"), ("xlsx", "Excel")],
        default="csv",
        help_text="Export format",
    )

    include_variants = serializers.BooleanField(
        default=True, help_text="Include product variants in export"
    )

    include_images = serializers.BooleanField(
        default=False, help_text="Include image URLs in export"
    )

    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Filter by category IDs",
    )

    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, help_text="Filter by tag IDs"
    )

    is_active = serializers.BooleanField(
        required=False, help_text="Filter by active status"
    )

    date_from = serializers.DateTimeField(
        required=False, help_text="Filter products created from this date"
    )

    date_to = serializers.DateTimeField(
        required=False, help_text="Filter products created until this date"
    )
