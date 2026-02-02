"""
Wishlist Serializers.
"""

from rest_framework import serializers

from apps.products.models import Wishlist, WishlistItem, Product


class WishlistItemSerializer(serializers.ModelSerializer):
    """Serializer for wishlist items."""
    
    product_id = serializers.UUIDField(write_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_price = serializers.DecimalField(
        source="product.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    product_compare_price = serializers.DecimalField(
        source="product.compare_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )
    product_image = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "product_slug",
            "product_price",
            "product_compare_price",
            "product_image",
            "variant_id",
            "notes",
            "priority",
            "notify_on_sale",
            "notify_on_restock",
            "is_available",
            "is_on_sale",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
    
    def get_product_image(self, obj):
        """Get primary product image URL."""
        primary_image = obj.product.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None
    
    def create(self, validated_data):
        """Create wishlist item."""
        product_id = validated_data.pop("product_id")
        product = Product.objects.get(id=product_id)
        validated_data["product"] = product
        return super().create(validated_data)


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlists."""
    
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
    share_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "description",
            "is_default",
            "is_public",
            "share_token",
            "share_url",
            "item_count",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "share_token", "created_at", "updated_at"]
    
    def get_share_url(self, obj):
        """Generate share URL for public wishlists."""
        if obj.is_public and obj.share_token:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/wishlist/shared/{obj.share_token}")
        return None


class WishlistSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for listing wishlists."""
    
    item_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = [
            "id",
            "name",
            "is_default",
            "is_public",
            "item_count",
            "created_at",
        ]


class AddToWishlistSerializer(serializers.Serializer):
    """Serializer for adding item to wishlist."""
    
    product_id = serializers.UUIDField()
    variant_id = serializers.UUIDField(required=False, allow_null=True)
    wishlist_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_product_id(self, value):
        """Validate product exists."""
        if not Product.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Product not found or inactive")
        return value


class MoveWishlistItemSerializer(serializers.Serializer):
    """Serializer for moving item between wishlists."""
    
    item_id = serializers.UUIDField()
    target_wishlist_id = serializers.UUIDField()
