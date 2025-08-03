"""
Base permission classes for the Bazary API.

This module provides reusable permission classes that can be used across
different apps to implement consistent authorization logic.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission

# Import permission classes from submodules
from .user import (
    UserManagementPermission,
    ProfilePermission,
    PasswordChangePermission,
    UserRolePermission,
    UserActivationPermission,
)
from .product import (
    ProductPermission,
    ProductOwnershipPermission,
    ProductBulkOperationPermission,
    ProductAnalyticsPermission,
)
from .mixins import (
    OwnershipMixin,
    AdminAccessMixin,
    ReadOnlyMixin,
    AuthenticationMixin,
    CombinedPermissionMixin,
)


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow owners and admins to edit, others read-only.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for all
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions for owner or admin
        return obj.owner == request.user or request.user.is_staff


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admins to edit, others read-only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsAdminOrOwner(BasePermission):
    """
    Permission for admin users or object owners (no read-only access).
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_staff:
            return True

        # Owner can access their own objects
        return hasattr(obj, "owner") and obj.owner == request.user


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Custom permission to allow authenticated users to write, others read-only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated


class IsSuperUserOnly(BasePermission):
    """
    Permission for superuser access only.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsStaffOrOwner(BasePermission):
    """
    Permission for staff users or object owners.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can access everything
        if request.user.is_staff:
            return True

        # Owner can access their own objects
        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "owner"):
            return obj.owner == request.user
        elif hasattr(obj, "created_by"):
            return obj.created_by == request.user

        return False
