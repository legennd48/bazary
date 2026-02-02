"""
Vendor serializers for multi-vendor marketplace.
"""

from rest_framework import serializers
from apps.authentication.models import Vendor, VendorDocument, VendorApplication


class VendorDocumentSerializer(serializers.ModelSerializer):
    """Serializer for vendor documents."""

    class Meta:
        model = VendorDocument
        fields = [
            'id', 'document_type', 'file', 'description',
            'status', 'review_notes', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'review_notes', 'created_at']


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for vendor profile."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    documents = VendorDocumentSerializer(many=True, read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    can_sell = serializers.BooleanField(read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'id', 'user_email', 'user_name',
            'store_name', 'slug', 'store_description', 'logo', 'banner',
            'vendor_type', 'business_name', 'business_registration_number', 'tax_id',
            'business_email', 'business_phone', 'website',
            'address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country',
            'verification_status', 'is_verified', 'can_sell',
            'is_active', 'is_featured',
            'accepts_returns', 'return_policy', 'shipping_policy',
            'total_products', 'total_orders', 'average_rating', 'total_reviews',
            'documents', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'verification_status', 'is_verified', 'can_sell',
            'is_active', 'is_featured', 'total_products', 'total_orders',
            'average_rating', 'total_reviews', 'created_at', 'updated_at'
        ]


class VendorPublicSerializer(serializers.ModelSerializer):
    """Public-facing vendor serializer (for customers viewing stores)."""

    class Meta:
        model = Vendor
        fields = [
            'id', 'store_name', 'slug', 'store_description', 'logo', 'banner',
            'city', 'country', 'is_verified', 'is_featured',
            'total_products', 'average_rating', 'total_reviews',
            'accepts_returns', 'return_policy', 'shipping_policy',
        ]


class VendorApplicationSerializer(serializers.ModelSerializer):
    """Serializer for vendor applications."""

    class Meta:
        model = VendorApplication
        fields = [
            'id', 'store_name', 'vendor_type', 'business_description',
            'product_categories', 'expected_monthly_sales',
            'contact_email', 'contact_phone',
            'status', 'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'rejection_reason', 'created_at', 'updated_at']


class VendorApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating vendor applications."""

    class Meta:
        model = VendorApplication
        fields = [
            'store_name', 'vendor_type', 'business_description',
            'product_categories', 'expected_monthly_sales',
            'contact_email', 'contact_phone',
        ]

    def validate_store_name(self, value):
        # Check if store name is already taken
        if Vendor.objects.filter(store_name__iexact=value).exists():
            raise serializers.ValidationError("This store name is already taken.")
        if VendorApplication.objects.filter(
            store_name__iexact=value,
            status__in=['submitted', 'under_review']
        ).exists():
            raise serializers.ValidationError("An application with this store name is already pending.")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'submitted'
        return super().create(validated_data)


class VendorRegistrationSerializer(serializers.Serializer):
    """
    Complete vendor registration (creates application + basic vendor profile).
    """

    # Application fields
    store_name = serializers.CharField(max_length=255)
    vendor_type = serializers.ChoiceField(choices=Vendor.VENDOR_TYPE)
    business_description = serializers.CharField()
    product_categories = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    # Contact
    contact_email = serializers.EmailField()
    contact_phone = serializers.CharField(max_length=20)

    # Optional business details
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    business_registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)

    # Address
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, default='Ethiopia')

    def validate_store_name(self, value):
        if Vendor.objects.filter(store_name__iexact=value).exists():
            raise serializers.ValidationError("This store name is already taken.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user

        # Check if user already has a vendor profile
        if hasattr(user, 'vendor_profile'):
            raise serializers.ValidationError({
                'non_field_errors': ['You already have a vendor profile.']
            })

        # Check for pending applications
        if VendorApplication.objects.filter(
            user=user,
            status__in=['submitted', 'under_review']
        ).exists():
            raise serializers.ValidationError({
                'non_field_errors': ['You already have a pending vendor application.']
            })

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user

        # Create the vendor profile (inactive, pending verification)
        vendor = Vendor.objects.create(
            user=user,
            store_name=validated_data['store_name'],
            store_description=validated_data.get('business_description', ''),
            vendor_type=validated_data['vendor_type'],
            business_name=validated_data.get('business_name', ''),
            business_registration_number=validated_data.get('business_registration_number', ''),
            business_email=validated_data['contact_email'],
            business_phone=validated_data['contact_phone'],
            city=validated_data.get('city', ''),
            country=validated_data.get('country', 'Ethiopia'),
            verification_status='pending',
            is_active=False,
        )

        # Create the application record
        application = VendorApplication.objects.create(
            user=user,
            vendor=vendor,
            store_name=validated_data['store_name'],
            vendor_type=validated_data['vendor_type'],
            business_description=validated_data['business_description'],
            product_categories=validated_data.get('product_categories', []),
            contact_email=validated_data['contact_email'],
            contact_phone=validated_data['contact_phone'],
            status='submitted',
        )

        # Update user role to indicate vendor status
        user.role = 'vendor'
        user.save(update_fields=['role'])

        return vendor


class AdminVendorVerificationSerializer(serializers.Serializer):
    """Serializer for admin vendor verification actions."""

    action = serializers.ChoiceField(choices=['approve', 'reject', 'request_documents', 'suspend'])
    notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting an application.'
            })
        return attrs
