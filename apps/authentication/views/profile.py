"""
Enhanced profile management views.
"""

from django.contrib.auth import get_user_model

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.capture_decorator import capture_for_swagger
from apps.core.permissions import ProfilePermission
from apps.core.swagger_docs import SwaggerTags

from ..models import UserAddress, UserProfile
from ..serializers import (
    EnhancedUserSerializer,
    UserActivitySerializer,
    UserAddressSerializer,
    UserProfileSerializer,
)
from ..utils import log_user_activity

User = get_user_model()


class EnhancedProfileView(APIView):
    """
    ## Enhanced User Profile Management

    Comprehensive profile management with extended user information.

    ### 👤 Features
    - **Complete Profile**: Basic info + extended profile data
    - **Privacy Settings**: Control profile visibility
    - **Preferences**: Notification and display preferences
    - **Statistics**: Profile completion and activity metrics
    - **Avatar Upload**: Profile picture management

    ### 🔐 Security
    - User can only access their own profile
    - Secure file upload handling
    - Activity logging for profile changes
    """

    permission_classes = [ProfilePermission]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get Complete User Profile",
        operation_description="""
        Retrieve complete user profile including basic info and extended profile data.
        
        ### Response Includes:
        - Basic user information (name, email, phone)
        - Extended profile data (bio, preferences, privacy settings)
        - Profile completion statistics
        - User addresses
        - Account security information
        """,
        responses={
            200: openapi.Response("Complete profile data", EnhancedUserSerializer),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    @capture_for_swagger("enhanced_profile_get")
    def get(self, request):
        """Get complete user profile."""
        serializer = EnhancedUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Update Complete User Profile",
        operation_description="""
        Update user profile information including basic and extended data.
        
        ### Updatable Basic Fields:
        - first_name, last_name
        - phone_number
        - date_of_birth
        - avatar (file upload)
        
        ### Updatable Profile Fields:
        - bio, gender, website, location
        - timezone, language
        - notification preferences
        - privacy settings
        - marketing preferences
        
        ### Note:
        This endpoint accepts multipart/form-data for file uploads.
        All fields are optional and can be updated individually.
        """,
        responses={
            200: openapi.Response(
                "Profile updated successfully", EnhancedUserSerializer
            ),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    @capture_for_swagger("enhanced_profile_update")
    def patch(self, request):
        """Update user profile."""
        user = request.user
        user_data = {}
        profile_data = {}

        # Separate user and profile fields
        user_fields = [
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "avatar",
        ]
        profile_fields = [
            "bio",
            "gender",
            "website",
            "location",
            "timezone",
            "language",
            "notification_preference",
            "is_profile_public",
            "show_email",
            "show_phone",
            "marketing_emails",
            "product_updates",
            "newsletter",
        ]

        for field in user_fields:
            if field in request.data:
                user_data[field] = request.data[field]

        for field in profile_fields:
            if field in request.data:
                profile_data[field] = request.data[field]

        # Update user fields
        if user_data:
            user_serializer = EnhancedUserSerializer(user, data=user_data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()
            else:
                return Response(
                    user_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # Update profile fields
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile_serializer = UserProfileSerializer(
                profile, data=profile_data, partial=True
            )
            if profile_serializer.is_valid():
                profile_serializer.save()
            else:
                return Response(
                    profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        # Log profile update
        log_user_activity(
            user=user,
            action="profile_update",
            description="Profile updated successfully",
            request=request,
            metadata={
                "updated_user_fields": list(user_data.keys()),
                "updated_profile_fields": list(profile_data.keys()),
            },
        )

        # Return updated profile
        updated_user = User.objects.get(id=user.id)
        serializer = EnhancedUserSerializer(updated_user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    ## User Address Management

    Manage shipping and billing addresses for users.

    ### 📍 Features
    - **Multiple Addresses**: Support for multiple shipping/billing addresses
    - **Default Addresses**: Set default address per type
    - **Address Validation**: Comprehensive address field validation
    - **Address Types**: Shipping, billing, or both

    ### 🔐 Security
    - Users can only access their own addresses
    - Address data validation and sanitization
    """

    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get addresses for current user only."""
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
        return UserAddress.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="List User Addresses",
        operation_description="""
        Retrieve all addresses for the current user.
        
        ### Query Parameters:
        - `address_type`: Filter by address type (shipping, billing, both)
        - `is_default`: Filter by default status (true/false)
        """,
        manual_parameters=[
            openapi.Parameter(
                "address_type",
                openapi.IN_QUERY,
                description="Filter by address type",
                type=openapi.TYPE_STRING,
                enum=["shipping", "billing", "both"],
            ),
            openapi.Parameter(
                "is_default",
                openapi.IN_QUERY,
                description="Filter by default status",
                type=openapi.TYPE_BOOLEAN,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List user addresses with filtering."""
        queryset = self.get_queryset()

        # Filter by address type
        address_type = request.query_params.get("address_type")
        if address_type:
            queryset = queryset.filter(address_type=address_type)

        # Filter by default status
        is_default = request.query_params.get("is_default")
        if is_default is not None:
            is_default = is_default.lower() == "true"
            queryset = queryset.filter(is_default=is_default)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Create New Address",
        operation_description="""
        Create a new address for the current user.
        
        ### Address Types:
        - `shipping`: For product deliveries
        - `billing`: For payment processing
        - `both`: Use for both shipping and billing
        
        ### Default Address Logic:
        - Setting `is_default=true` will remove default status from other addresses of the same type
        - Each user can have one default address per type
        """,
    )
    def create(self, request, *args, **kwargs):
        """Create new address."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            address = serializer.save()

            # Log address creation
            log_user_activity(
                user=request.user,
                action="profile_update",
                description=f"New {address.get_address_type_display().lower()} address added",
                request=request,
                metadata={
                    "address_id": str(address.id),
                    "address_type": address.address_type,
                    "is_default": address.is_default,
                },
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Set Default Address",
        operation_description="""
        Set an address as the default for its type.
        
        This will automatically remove the default status from any other
        address of the same type for this user.
        """,
    )
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """Set address as default."""
        address = self.get_object()

        # Remove default from other addresses of same type
        UserAddress.objects.filter(
            user=request.user, address_type=address.address_type, is_default=True
        ).exclude(pk=address.pk).update(is_default=False)

        # Set this address as default
        address.is_default = True
        address.save()

        # Log the change
        log_user_activity(
            user=request.user,
            action="profile_update",
            description=f"Set {address.get_address_type_display().lower()} address as default",
            request=request,
            metadata={
                "address_id": str(address.id),
                "address_type": address.address_type,
            },
        )

        serializer = self.get_serializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserActivityView(APIView):
    """
    ## User Activity History

    View user's own activity history for account transparency.

    ### 📊 Features
    - **Activity Tracking**: Complete activity history
    - **Security Monitoring**: Login attempts and security events
    - **Profile Changes**: Track profile modifications
    - **Transparency**: Users can see their own activity

    ### 🔐 Privacy
    - Users can only see their own activities
    - Sensitive information is filtered out
    - Activity data helps users monitor account security
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Activity History",
        operation_description="""
        Retrieve activity history for the current user.
        
        ### Query Parameters:
        - `action`: Filter by activity type
        - `days`: Number of days to look back (default: 30)
        - `limit`: Maximum number of activities to return (default: 50)
        
        ### Activity Types:
        - login, logout, password_change, password_reset
        - email_verification, profile_update, avatar_upload
        - account_activation, account_deactivation
        """,
        manual_parameters=[
            openapi.Parameter(
                "action",
                openapi.IN_QUERY,
                description="Filter by activity type",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "days",
                openapi.IN_QUERY,
                description="Days to look back (default: 30)",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Max activities to return (default: 50)",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    )
    def get(self, request):
        """Get user activity history."""
        from datetime import timedelta

        from django.utils import timezone

        user = request.user
        queryset = user.activities.all()

        # Filter by action type
        action = request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        # Filter by date range
        days = int(request.query_params.get("days", 30))
        if days > 0:
            since_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(timestamp__gte=since_date)

        # Limit results
        limit = int(request.query_params.get("limit", 50))
        if limit > 100:  # Prevent excessive data requests
            limit = 100

        activities = queryset[:limit]
        serializer = UserActivitySerializer(activities, many=True)

        return Response(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "total_activities": queryset.count(),
                "activities": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
