"""
Categories serializers.
"""

from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    full_name = serializers.CharField(read_only=True)
    has_children = serializers.BooleanField(read_only=True)
    subcategories = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "is_active",
            "sort_order",
            "full_name",
            "has_children",
            "subcategories",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_subcategories(self, obj):
        """Get subcategories if requested."""
        request = self.context.get("request")
        if request and request.query_params.get("include_subcategories"):
            subcategories = obj.subcategories.filter(is_active=True)
            return CategorySerializer(
                subcategories, many=True, context=self.context
            ).data
        return []

    def get_products_count(self, obj):
        """Get number of products in this category."""
        return obj.products.filter(is_active=True).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for category tree structure."""

    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "sort_order",
            "subcategories",
        ]

    def get_subcategories(self, obj):
        """Recursively get all subcategories."""
        subcategories = obj.subcategories.filter(is_active=True)
        return CategoryTreeSerializer(subcategories, many=True).data


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories."""

    class Meta:
        model = Category
        fields = ["name", "description", "image", "parent", "is_active", "sort_order"]

    def validate_parent(self, value):
        """Validate parent category."""
        if value and not value.is_active:
            raise serializers.ValidationError("Cannot set inactive category as parent.")
        return value
