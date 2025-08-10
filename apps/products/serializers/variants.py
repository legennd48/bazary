"""
Enhanced serializers for product variants.
"""

from rest_framework import serializers

from apps.products.models import (
    ProductVariant,
    ProductVariantImage,
    ProductVariantOption,
    VariantOption,
    VariantOptionValue,
)


class VariantOptionSerializer(serializers.ModelSerializer):
    """Serializer for VariantOption model."""

    values_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VariantOption
        fields = [
            "id",
            "name",
            "display_name",
            "display_type",
            "is_required",
            "sort_order",
            "values_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VariantOptionValueSerializer(serializers.ModelSerializer):
    """Serializer for VariantOptionValue model."""

    option_name = serializers.CharField(source="option.name", read_only=True)

    class Meta:
        model = VariantOptionValue
        fields = [
            "id",
            "option",
            "option_name",
            "value",
            "display_name",
            "color_code",
            "image",
            "sort_order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class VariantOptionValueDetailSerializer(VariantOptionValueSerializer):
    """Detailed serializer for VariantOptionValue with option details."""

    option = VariantOptionSerializer(read_only=True)

    class Meta(VariantOptionValueSerializer.Meta):
        pass


class ProductVariantImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariantImage model."""

    class Meta:
        model = ProductVariantImage
        fields = [
            "id",
            "image",
            "alt_text",
            "is_primary",
            "sort_order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ProductVariantOptionSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariantOption model."""

    option_name = serializers.CharField(source="option.display_name", read_only=True)
    value_name = serializers.CharField(source="value.display_name", read_only=True)
    value_color = serializers.CharField(source="value.color_code", read_only=True)
    option_display_type = serializers.CharField(
        source="option.display_type", read_only=True
    )

    class Meta:
        model = ProductVariantOption
        fields = [
            "id",
            "option",
            "option_name",
            "option_display_type",
            "value",
            "value_name",
            "value_color",
        ]
        read_only_fields = ["id"]


class ProductVariantListSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant list view."""

    option_values = ProductVariantOptionSerializer(many=True, read_only=True)
    primary_image = ProductVariantImageSerializer(read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_in_stock = serializers.BooleanField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "sku",
            "price",
            "compare_price",
            "effective_price",
            "stock_quantity",
            "is_active",
            "is_in_stock",
            "is_low_stock",
            "discount_percentage",
            "option_values",
            "primary_image",
            "created_at",
        ]
        read_only_fields = ["id", "sku", "created_at"]


class ProductVariantDetailSerializer(ProductVariantListSerializer):
    """Serializer for ProductVariant detail view."""

    images = ProductVariantImageSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)

    class Meta(ProductVariantListSerializer.Meta):
        fields = ProductVariantListSerializer.Meta.fields + [
            "product_name",
            "product_slug",
            "compare_price",
            "cost_price",
            "low_stock_threshold",
            "weight",
            "dimensions_length",
            "dimensions_width",
            "dimensions_height",
            "images",
            "updated_at",
        ]


class ProductVariantCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ProductVariant."""

    option_values_data = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        write_only=True,
        required=False,
        help_text="List of option-value pairs: [{'option': 1, 'value': 2}, ...]",
    )

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product",
            "price",
            "compare_price",
            "cost_price",
            "stock_quantity",
            "low_stock_threshold",
            "is_active",
            "weight",
            "dimensions_length",
            "dimensions_width",
            "dimensions_height",
            "option_values_data",
        ]
        read_only_fields = ["id", "sku"]

    def create(self, validated_data):
        """Create variant with option values."""
        option_values_data = validated_data.pop("option_values_data", [])
        variant = ProductVariant.objects.create(**validated_data)

        # Create option values
        for option_value_data in option_values_data:
            ProductVariantOption.objects.create(
                variant=variant,
                option_id=option_value_data["option"],
                value_id=option_value_data["value"],
            )

        return variant

    def update(self, instance, validated_data):
        """Update variant and option values."""
        option_values_data = validated_data.pop("option_values_data", None)

        # Update variant fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update option values if provided
        if option_values_data is not None:
            # Remove existing option values
            instance.option_values.all().delete()

            # Create new option values
            for option_value_data in option_values_data:
                ProductVariantOption.objects.create(
                    variant=instance,
                    option_id=option_value_data["option"],
                    value_id=option_value_data["value"],
                )

        return instance

    def validate_option_values_data(self, value):
        """Validate option values data."""
        if not value:
            return value

        seen_options = set()
        for option_value in value:
            if "option" not in option_value or "value" not in option_value:
                raise serializers.ValidationError(
                    "Each option_value must contain 'option' and 'value' keys"
                )

            option_id = option_value["option"]
            if option_id in seen_options:
                raise serializers.ValidationError(f"Duplicate option {option_id} found")
            seen_options.add(option_id)

            # Validate that value belongs to option
            try:
                option = VariantOption.objects.get(id=option_id)
                value_obj = VariantOptionValue.objects.get(id=option_value["value"])
                if value_obj.option != option:
                    raise serializers.ValidationError(
                        f"Value {value_obj.id} does not belong to option {option_id}"
                    )
            except (VariantOption.DoesNotExist, VariantOptionValue.DoesNotExist):
                raise serializers.ValidationError("Invalid option or value ID")

        return value


class VariantOptionWithValuesSerializer(VariantOptionSerializer):
    """Serializer for VariantOption with its values."""

    values = VariantOptionValueSerializer(many=True, read_only=True)

    class Meta(VariantOptionSerializer.Meta):
        fields = VariantOptionSerializer.Meta.fields + ["values"]
