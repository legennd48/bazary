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
        if hasattr(view, 'action') and view.action == 'create':
            return request.user.is_authenticated and request.user.is_staff
        
        # List users - admin only
        if hasattr(view, 'action') and view.action == 'list':
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
        if hasattr(obj, 'user'):
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
