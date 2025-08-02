"""
Product-specific permission classes.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission


class ProductPermission(BasePermission):
    """
    Custom permission for product management.
    
    - List/Read: All users (including anonymous)
    - Create/Update/Delete: Admin users only
    - Search/Filter: All users
    """

    def has_permission(self, request, view):
        # Allow all users to read products
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow search actions for all users
        if hasattr(view, 'action') and view.action in ['search', 'featured', 'in_stock', 'by_category']:
            return True
        
        # Only authenticated admin users can create/update/delete
        return request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Allow all users to read individual products
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Only admin users can modify products
        return request.user.is_authenticated and request.user.is_staff


class ProductOwnershipPermission(BasePermission):
    """
    Permission for product ownership (future multi-vendor support).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read access for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin can modify any product
        if request.user.is_staff:
            return True
        
        # Future: Product owner can modify their own products
        # return obj.owner == request.user
        
        # For now, only admin can modify
        return False


class ProductBulkOperationPermission(BasePermission):
    """
    Permission for bulk product operations.
    """

    def has_permission(self, request, view):
        # Only authenticated admin users can perform bulk operations
        return request.user.is_authenticated and request.user.is_staff


class ProductAnalyticsPermission(BasePermission):
    """
    Permission for product analytics and reporting.
    """

    def has_permission(self, request, view):
        # Basic analytics available to all users
        if hasattr(view, 'action') and view.action in ['popular', 'trending']:
            return True
        
        # Detailed analytics only for admin users
        return request.user.is_authenticated and request.user.is_staff
