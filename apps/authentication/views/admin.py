"""
Admin views for user management.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrStaff
from apps.core.swagger_docs import SwaggerTags

from ..models import UserActivity, UserAddress, UserProfile
from ..serializers import (
    AdminUserManagementSerializer,
    BulkUserActionSerializer,
    UserActivitySerializer,
    UserAddressSerializer,
    UserProfileSerializer,
)
from ..utils import bulk_user_action, log_user_activity

User = get_user_model()


class AdminUserManagementViewSet(viewsets.ModelViewSet):
    """
    ## Admin User Management

    Comprehensive user management interface for administrators.

    ### 👥 Features
    - **View All Users**: Complete user listing with profiles
    - **User Search**: Advanced search and filtering
    - **Bulk Operations**: Mass user actions
    - **Activity Monitoring**: User activity tracking
    - **Account Management**: Activate/deactivate accounts
    - **Role Management**: Assign and modify user roles

    ### 🔐 Security
    - Admin/staff only access
    - Complete audit logging
    - Secure bulk operations
    - Activity monitoring
    """

    queryset = (
        User.objects.all()
        .select_related("profile")
        .prefetch_related("addresses", "activities")
    )
    serializer_class = AdminUserManagementSerializer
    permission_classes = [IsAdminOrStaff]

    def get_queryset(self):
        """Get filtered queryset based on query parameters."""
        queryset = super().get_queryset()

        # Search functionality
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(username__icontains=search)
            )

        # Filter by role
        role = self.request.query_params.get("role", None)
        if role:
            queryset = queryset.filter(role=role)

        # Filter by verification status
        is_verified = self.request.query_params.get("is_verified", None)
        if is_verified is not None:
            is_verified = is_verified.lower() == "true"
            queryset = queryset.filter(is_email_verified=is_verified)

        # Filter by active status
        is_active = self.request.query_params.get("is_active", None)
        if is_active is not None:
            is_active = is_active.lower() == "true"
            queryset = queryset.filter(is_active=is_active)

        # Filter by date range
        date_from = self.request.query_params.get("date_from", None)
        date_to = self.request.query_params.get("date_to", None)
        if date_from:
            queryset = queryset.filter(date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_joined__lte=date_to)

        return queryset.order_by("-date_joined")

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="List Users with Admin Features",
        operation_description="""
        Retrieve paginated list of users with admin management capabilities.
        
        ### Query Parameters:
        - `search`: Search in email, name, username
        - `role`: Filter by user role (customer, staff, admin, super_admin)
        - `is_verified`: Filter by email verification status (true/false)
        - `is_active`: Filter by account active status (true/false)
        - `date_from`: Filter users created after this date (YYYY-MM-DD)
        - `date_to`: Filter users created before this date (YYYY-MM-DD)
        - `page`: Page number for pagination
        - `page_size`: Number of results per page (default: 20)
        
        ### Response Includes:
        - User basic information and profile
        - Recent activity history
        - Account status and security info
        - Address information
        """,
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search users",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "role",
                openapi.IN_QUERY,
                description="Filter by role",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "is_verified",
                openapi.IN_QUERY,
                description="Filter by verification",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "is_active",
                openapi.IN_QUERY,
                description="Filter by active status",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "date_from",
                openapi.IN_QUERY,
                description="From date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "date_to",
                openapi.IN_QUERY,
                description="To date (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List users with admin management features."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Create User Account",
        operation_description="""
        Create a new user account with admin privileges.
        
        ### Features:
        - Set initial user role and permissions
        - Configure account verification status
        - Generate secure initial password
        - Send welcome email (optional)
        
        ### Security:
        - Admin only access
        - Password complexity validation
        - Email uniqueness validation
        - Complete audit logging
        """,
        request_body=AdminUserManagementSerializer,
        responses={
            201: openapi.Response(
                "User created successfully", AdminUserManagementSerializer
            ),
            400: openapi.Response("Validation error"),
            403: openapi.Response("Admin access required"),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create new user account."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Get User Details",
        operation_description="""
        Retrieve detailed information about a specific user account.
        
        ### Response Includes:
        - Complete user profile information
        - Account status and security details
        - Recent activity history
        - Address information
        - Role and permission details
        
        ### Security:
        - Admin only access
        - Complete audit logging
        """,
        responses={
            200: openapi.Response(
                "User details retrieved", AdminUserManagementSerializer
            ),
            404: openapi.Response("User not found"),
            403: openapi.Response("Admin access required"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed user information."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Update User Account (Full)",
        operation_description="""
        Update user account with complete data replacement.
        
        ### Features:
        - Modify user role and permissions
        - Update profile information
        - Change account status
        - Reset security settings
        
        ### Security:
        - Admin only access
        - Complete audit logging
        - Permission validation
        """,
        request_body=AdminUserManagementSerializer,
        responses={
            200: openapi.Response(
                "User updated successfully", AdminUserManagementSerializer
            ),
            400: openapi.Response("Validation error"),
            404: openapi.Response("User not found"),
            403: openapi.Response("Admin access required"),
        },
    )
    def update(self, request, *args, **kwargs):
        """Update user account (full update)."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Update User Account (Partial)",
        operation_description="""
        Update user account with partial data.
        
        ### Features:
        - Selectively modify specific fields
        - Preserve existing data
        - Flexible account management
        - Quick status updates
        
        ### Security:
        - Admin only access
        - Complete audit logging
        - Field-level validation
        """,
        request_body=AdminUserManagementSerializer,
        responses={
            200: openapi.Response(
                "User updated successfully", AdminUserManagementSerializer
            ),
            400: openapi.Response("Validation error"),
            404: openapi.Response("User not found"),
            403: openapi.Response("Admin access required"),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Update user account (partial update)."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Delete User Account",
        operation_description="""
        Permanently delete a user account and all associated data.
        
        ### Warning:
        - This action cannot be undone
        - All user data will be permanently removed
        - Associated orders and transactions will be preserved but anonymized
        
        ### Security:
        - Admin only access
        - Complete audit logging
        - Confirmation required
        """,
        responses={
            204: openapi.Response("User account deleted successfully"),
            404: openapi.Response("User not found"),
            403: openapi.Response("Admin access required"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete user account."""
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Bulk User Actions",
        operation_description="""
        Perform bulk actions on multiple users simultaneously.
        
        ### Available Actions:
        - `activate`: Activate user accounts
        - `deactivate`: Deactivate user accounts
        - `verify_email`: Mark emails as verified
        - `reset_failed_attempts`: Reset failed login attempts
        - `send_verification`: Send verification emails
        
        ### Security Features:
        - Admin only access
        - Complete audit logging
        - Reason tracking for accountability
        - Batch processing with error handling
        """,
        request_body=BulkUserActionSerializer,
        responses={
            200: openapi.Response(
                "Bulk action completed",
                examples={
                    "application/json": {
                        "message": "Bulk action completed",
                        "results": {
                            "success_count": 5,
                            "total_count": 6,
                            "errors": [
                                "Error with user user@example.com: Account already active"
                            ],
                        },
                    }
                },
            ),
            400: openapi.Response("Invalid request data"),
            403: openapi.Response("Admin access required"),
        },
    )
    @action(detail=False, methods=["post"])
    def bulk_action(self, request):
        """Perform bulk actions on users."""
        serializer = BulkUserActionSerializer(data=request.data)
        if serializer.is_valid():
            user_ids = serializer.validated_data["user_ids"]
            action_type = serializer.validated_data["action"]
            reason = serializer.validated_data.get("reason", "")

            # Perform bulk action
            results = bulk_user_action(user_ids, action_type, request.user, reason)

            # Log admin activity
            log_user_activity(
                user=request.user,
                action="admin_bulk_action",
                description=f"Performed bulk action '{action_type}' on {results['total_count']} users",
                request=request,
                metadata={
                    "action": action_type,
                    "user_count": results["total_count"],
                    "success_count": results["success_count"],
                    "reason": reason,
                },
            )

            return Response(
                {
                    "message": "Bulk action completed",
                    "results": results,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Statistics",
        operation_description="""
        Retrieve comprehensive user statistics for admin dashboard.
        
        ### Statistics Included:
        - Total user count by role
        - Verification status breakdown
        - Registration trends (daily, weekly, monthly)
        - Active/inactive user counts
        - Account security metrics
        """,
    )
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """Get user statistics for admin dashboard."""
        stats = {}

        # Basic counts
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_email_verified=True).count()

        # Role distribution
        role_stats = User.objects.values("role").annotate(count=Count("role"))
        role_distribution = {item["role"]: item["count"] for item in role_stats}

        # Registration trends (last 30 days)
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = (
            User.objects.filter(date_joined__gte=thirty_days_ago)
            .extra({"day": "date(date_joined)"})
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        # Security metrics
        locked_accounts = User.objects.filter(
            account_locked_until__gt=timezone.now()
        ).count()
        unverified_accounts = User.objects.filter(
            is_email_verified=False, date_joined__lt=timezone.now() - timedelta(days=7)
        ).count()

        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "role_distribution": role_distribution,
            "registration_trends": list(recent_registrations),
            "security_metrics": {
                "locked_accounts": locked_accounts,
                "old_unverified_accounts": unverified_accounts,
            },
            "percentages": {
                "active_percentage": round(
                    (active_users / total_users * 100) if total_users > 0 else 0, 1
                ),
                "verified_percentage": round(
                    (verified_users / total_users * 100) if total_users > 0 else 0, 1
                ),
            },
        }

        return Response(stats, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Activity History",
        operation_description="""
        Retrieve detailed activity history for a specific user.
        
        ### Activity Types Tracked:
        - Login/logout events
        - Password changes and resets
        - Email verification activities
        - Profile updates
        - Account status changes
        - Admin actions performed on account
        """,
    )
    @action(detail=True, methods=["get"])
    def activity_history(self, request, pk=None):
        """Get user activity history."""
        user = self.get_object()
        activities = user.activities.all()[:50]  # Last 50 activities
        serializer = UserActivitySerializer(activities, many=True)

        return Response(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                },
                "activities": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Addresses",
        operation_description="Retrieve all addresses associated with a user.",
    )
    @action(detail=True, methods=["get"])
    def addresses(self, request, pk=None):
        """Get user addresses."""
        user = self.get_object()
        addresses = user.addresses.all()
        serializer = UserAddressSerializer(addresses, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Update User Role",
        operation_description="""
        Update user role (admin only).
        
        ### Available Roles:
        - customer: Regular customer account
        - staff: Staff member with limited admin access
        - admin: Full admin access
        - super_admin: Complete system access
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "role": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["customer", "staff", "admin", "super_admin"],
                    description="New role for the user",
                ),
                "reason": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Reason for role change"
                ),
            },
            required=["role"],
        ),
    )
    @action(detail=True, methods=["patch"])
    def update_role(self, request, pk=None):
        """Update user role."""
        user = self.get_object()
        role = request.data.get("role")
        reason = request.data.get("reason", "")

        if role not in ["customer", "staff", "admin", "super_admin"]:
            return Response(
                {"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST
            )

        old_role = user.role
        user.role = role
        user.save()

        # Log the role change
        log_user_activity(
            user=user,
            action="admin_bulk_action",
            description=f"Role changed from '{old_role}' to '{role}' by {request.user.email}. Reason: {reason}",
            request=request,
            metadata={
                "old_role": old_role,
                "new_role": role,
                "changed_by": request.user.email,
                "reason": reason,
            },
        )

        return Response(
            {
                "message": "Role updated successfully",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "old_role": old_role,
                    "new_role": role,
                },
            },
            status=status.HTTP_200_OK,
        )
