"""
Products serializers.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Product, ProductImage, Tag
from apps.categories.serializers import CategorySerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'image', 'alt_text', 'is_primary', 'sort_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view (minimal fields)."""
    
    category = CategorySerializer(read_only=True)
    primary_image = ProductImageSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'price', 
            'compare_price', 'category', 'primary_image', 'tags',
            'is_featured', 'is_in_stock', 'discount_percentage',
            'created_at'
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
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'sku', 'price', 'compare_price', 'category', 'tags',
            'track_inventory', 'stock_quantity', 'low_stock_threshold',
            'is_active', 'is_featured', 'is_digital', 'meta_title',
            'meta_description', 'images', 'is_in_stock', 'is_low_stock',
            'discount_percentage', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'sku', 'created_by', 'created_at', 'updated_at'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products."""
    
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of tag IDs to associate with the product"
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'short_description', 'price',
            'compare_price', 'cost_price', 'category', 'tag_ids',
            'track_inventory', 'stock_quantity', 'low_stock_threshold',
            'is_active', 'is_featured', 'is_digital', 'meta_title',
            'meta_description'
        ]
        read_only_fields = ['id']
    
    def validate_price(self, value):
        """Validate that price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_compare_price(self, value):
        """Validate that compare price is greater than price if provided."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Compare price must be greater than zero.")
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        price = attrs.get('price')
        compare_price = attrs.get('compare_price')
        
        if compare_price and price and compare_price <= price:
            raise serializers.ValidationError(
                "Compare price must be greater than regular price."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create product with tags."""
        tag_ids = validated_data.pop('tag_ids', [])
        
        # Set created_by to current user
        validated_data['created_by'] = self.context['request'].user
        
        product = Product.objects.create(**validated_data)
        
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            product.tags.set(tags)
        
        return product
    
    def update(self, instance, validated_data):
        """Update product with tags."""
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            tags = Tag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        return instance


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for product search results."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'price',
            'category_name', 'primary_image_url', 'is_featured'
        ]
    
    def get_primary_image_url(self, obj):
        """Get primary image URL."""
        primary_image = obj.primary_image
        if primary_image and primary_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        return None
