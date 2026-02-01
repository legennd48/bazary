"""
Service Serializers.

Full serializer set for service API operations.
"""

from decimal import Decimal

from rest_framework import serializers

from .models import (
    PricingType,
    Service,
    ServiceAddon,
    ServiceCategory,
    ServiceImage,
    ServiceProvider,
    ServiceStatus,
)


class ServiceCategoryListSerializer(serializers.ModelSerializer):
    """Minimal category info for lists."""
    
    subcategory_count = serializers.SerializerMethodField()
    service_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "subcategory_count",
            "service_count",
        ]
        read_only_fields = ["id", "slug"]
    
    def get_subcategory_count(self, obj) -> int:
        return obj.subcategories.filter(is_active=True).count()
    
    def get_service_count(self, obj) -> int:
        return obj.services.filter(status=ServiceStatus.ACTIVE).count()


class ServiceCategoryDetailSerializer(serializers.ModelSerializer):
    """Full category details with hierarchy."""
    
    parent = ServiceCategoryListSerializer(read_only=True)
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    subcategories = ServiceCategoryListSerializer(many=True, read_only=True)
    
    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "parent_id",
            "subcategories",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class ServiceCategoryCreateSerializer(serializers.ModelSerializer):
    """Create/update category."""
    
    class Meta:
        model = ServiceCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "parent",
            "is_active",
            "sort_order",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "slug": {"required": False},
        }


class ServiceImageSerializer(serializers.ModelSerializer):
    """Service gallery images."""
    
    class Meta:
        model = ServiceImage
        fields = [
            "id",
            "image",
            "alt_text",
            "sort_order",
        ]
        read_only_fields = ["id"]


class ServiceAddonSerializer(serializers.ModelSerializer):
    """Service add-ons."""
    
    class Meta:
        model = ServiceAddon
        fields = [
            "id",
            "name",
            "description",
            "price",
            "duration_minutes",
            "is_active",
        ]
        read_only_fields = ["id"]


class ServiceProviderMinimalSerializer(serializers.ModelSerializer):
    """Minimal provider info for service lists."""
    
    provider_name = serializers.CharField(source="user.get_full_name", read_only=True)
    provider_email = serializers.EmailField(source="user.email", read_only=True)
    
    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "provider_name",
            "provider_email",
            "is_primary",
            "is_active",
        ]


class ServiceProviderDetailSerializer(serializers.ModelSerializer):
    """Full provider details."""
    
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    provider_name = serializers.CharField(source="user.get_full_name", read_only=True)
    provider_email = serializers.EmailField(source="user.email", read_only=True)
    effective_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    effective_duration = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "user_id",
            "provider_name",
            "provider_email",
            "is_primary",
            "is_active",
            "custom_price",
            "custom_duration",
            "bio",
            "effective_price",
            "effective_duration",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "provider_name",
            "provider_email",
            "effective_price",
            "effective_duration",
            "created_at",
        ]


class ServiceProviderCreateSerializer(serializers.ModelSerializer):
    """Create/update service provider assignment."""
    
    user_id = serializers.UUIDField()
    
    class Meta:
        model = ServiceProvider
        fields = [
            "id",
            "user_id",
            "is_primary",
            "is_active",
            "custom_price",
            "custom_duration",
            "bio",
        ]
        read_only_fields = ["id"]
    
    def validate_user_id(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(id=value, is_staff=True).exists():
            raise serializers.ValidationError("User must be a staff member")
        return value


class ServiceListSerializer(serializers.ModelSerializer):
    """Minimal service info for lists."""
    
    category_name = serializers.CharField(source="category.name", read_only=True)
    total_duration_minutes = serializers.IntegerField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    provider_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "category",
            "category_name",
            "status",
            "pricing_type",
            "price",
            "compare_price",
            "currency",
            "discount_percentage",
            "duration_minutes",
            "total_duration_minutes",
            "max_attendees",
            "requires_booking",
            "featured_image",
            "provider_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]
    
    def get_provider_count(self, obj) -> int:
        return obj.providers.filter(is_active=True).count()


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Full service details."""
    
    category = ServiceCategoryListSerializer(read_only=True)
    images = ServiceImageSerializer(many=True, read_only=True)
    addons = ServiceAddonSerializer(many=True, read_only=True)
    providers = ServiceProviderDetailSerializer(many=True, read_only=True)
    
    total_duration_minutes = serializers.IntegerField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
    )
    
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "category",
            "tags",
            "status",
            "is_active",
            "pricing_type",
            "price",
            "compare_price",
            "currency",
            "discount_percentage",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "total_duration_minutes",
            "max_attendees",
            "min_attendees",
            "requires_booking",
            "advance_booking_days",
            "min_notice_hours",
            "cancellation_policy",
            "free_cancellation_hours",
            "featured_image",
            "images",
            "addons",
            "providers",
            "meta_title",
            "meta_description",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]


class ServiceCreateSerializer(serializers.ModelSerializer):
    """Create/update service."""
    
    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "slug",
            "short_description",
            "description",
            "category",
            "tags",
            "status",
            "pricing_type",
            "price",
            "compare_price",
            "currency",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "max_attendees",
            "min_attendees",
            "requires_booking",
            "advance_booking_days",
            "min_notice_hours",
            "cancellation_policy",
            "free_cancellation_hours",
            "featured_image",
            "meta_title",
            "meta_description",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "slug": {"required": False},
            "description": {"required": True},
        }
    
    def validate(self, attrs):
        # Validate attendee settings
        min_attendees = attrs.get("min_attendees", 1)
        max_attendees = attrs.get("max_attendees", 1)
        
        if min_attendees > max_attendees:
            raise serializers.ValidationError({
                "min_attendees": "Minimum attendees cannot exceed maximum"
            })
        
        # Validate compare_price
        price = attrs.get("price", Decimal("0.00"))
        compare_price = attrs.get("compare_price")
        
        if compare_price and compare_price <= price:
            raise serializers.ValidationError({
                "compare_price": "Compare price must be greater than price"
            })
        
        return attrs
    
    def create(self, validated_data):
        # Set created_by from request
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        
        return super().create(validated_data)


class ServiceBulkActionSerializer(serializers.Serializer):
    """Bulk actions on services."""
    
    service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )
    action = serializers.ChoiceField(
        choices=[
            ("activate", "Activate"),
            ("deactivate", "Deactivate"),
            ("archive", "Archive"),
            ("delete", "Delete"),
        ]
    )
    
    def validate_service_ids(self, value):
        existing_count = Service.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError(
                "One or more service IDs are invalid"
            )
        return value
