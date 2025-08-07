"""
User management permission classes.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission


class UserManagementPermission(BasePermission):
    """
    Permission for user management operations.

    - List users: Admin only
    - View profile: Owner or Admin
    - Create user: Admin only (registration is separate)
    - Update user: Owner or Admin
    - Delete user: Admin only
    """

    def has_permission(self, request, view):
        # Registration is handled separately
        if hasattr(view, "action") and view.action == "create":
            return request.user.is_authenticated and request.user.is_staff

        # List users - admin only
        if hasattr(view, "action") and view.action == "list":
            return request.user.is_authenticated and request.user.is_staff

        # Other actions require authentication
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can access all user objects
        if request.user.is_staff:
            return True

        # Users can only access their own profile
        return obj == request.user


class ProfilePermission(BasePermission):
    """
    Permission for user profile operations.
    """

    def has_permission(self, request, view):
        # Profile access requires authentication
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can access all profiles
        if request.user.is_staff:
            return True

        # Users can only access their own profile
        if hasattr(obj, "user"):
            return obj.user == request.user

        return obj == request.user


class UserRolePermission(BasePermission):
    """
    Permission for user role management.
    """

    def has_permission(self, request, view):
        # Only admin users can manage roles
        return request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Only admin users can modify user roles
        return request.user.is_authenticated and request.user.is_staff


class PasswordChangePermission(BasePermission):
    """
    Permission for password change operations.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only change their own password
        # Admins can reset any user's password
        return obj == request.user or request.user.is_staff


class UserActivationPermission(BasePermission):
    """
    Permission for user account activation/deactivation.
    """

    def has_permission(self, request, view):
        # Only admin users can activate/deactivate accounts
        return request.user.is_authenticated and request.user.is_staff


class IsAdminOrStaff(BasePermission):
    """
    Permission for admin and staff users only.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff
            or request.user.has_role("admin")
            or request.user.has_role("super_admin")
        )


class EnhancedProfilePermission(BasePermission):
    """
    Enhanced permission for profile operations with role-based access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Super admin can access everything
        if request.user.has_role("super_admin"):
            return True

        # Admin can access all profiles for management
        if (
            request.user.has_role("admin")
            and request.method in permissions.SAFE_METHODS
        ):
            return True

        # Staff can view profiles but not modify
        if (
            request.user.has_role("staff")
            and request.method in permissions.SAFE_METHODS
        ):
            return True

        # Users can access their own profile
        if hasattr(obj, "user"):
            return obj.user == request.user

        return obj == request.user


class UserAddressPermission(BasePermission):
    """
    Permission for user address management.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can view all addresses
        if request.user.is_staff and request.method in permissions.SAFE_METHODS:
            return True

        # Users can only access their own addresses
        return obj.user == request.user


class UserActivityPermission(BasePermission):
    """
    Permission for user activity tracking.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can view all activities
        if request.user.is_staff:
            return True

        # Users can only view their own activities
        return obj.user == request.user


class BulkUserActionPermission(BasePermission):
    """
    Permission for bulk user operations.
    """

    def has_permission(self, request, view):
        # Only admin and super admin can perform bulk actions
        return request.user.is_authenticated and (
            request.user.has_role("admin") or request.user.has_role("super_admin")
        )
