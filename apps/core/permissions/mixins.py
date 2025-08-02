"""
Permission mixins for reusable permission logic.
"""

from rest_framework import permissions


class OwnershipMixin:
    """
    Mixin to add ownership-based permission logic.
    """
    
    owner_field = 'owner'  # Default owner field name
    
    def is_owner(self, request, obj):
        """Check if the request user is the owner of the object."""
        if not request.user.is_authenticated:
            return False
        
        owner_field = getattr(self, 'owner_field', 'owner')
        return getattr(obj, owner_field, None) == request.user


class AdminAccessMixin:
    """
    Mixin to add admin access logic.
    """
    
    def is_admin(self, request):
        """Check if the request user is an admin."""
        return request.user.is_authenticated and request.user.is_staff
    
    def is_superuser(self, request):
        """Check if the request user is a superuser."""
        return request.user.is_authenticated and request.user.is_superuser


class ReadOnlyMixin:
    """
    Mixin to add read-only access logic.
    """
    
    def is_read_only_request(self, request):
        """Check if the request is read-only (GET, HEAD, OPTIONS)."""
        return request.method in permissions.SAFE_METHODS


class AuthenticationMixin:
    """
    Mixin to add authentication checks.
    """
    
    def is_authenticated(self, request):
        """Check if the request user is authenticated."""
        return request.user.is_authenticated
    
    def is_anonymous(self, request):
        """Check if the request user is anonymous."""
        return not request.user.is_authenticated


class CombinedPermissionMixin(OwnershipMixin, AdminAccessMixin, ReadOnlyMixin, AuthenticationMixin):
    """
    Combined mixin with all common permission utilities.
    """
    
    def has_admin_or_owner_access(self, request, obj):
        """Check if user is admin or owner."""
        return self.is_admin(request) or self.is_owner(request, obj)
    
    def has_read_or_admin_access(self, request):
        """Check if request is read-only or user is admin."""
        return self.is_read_only_request(request) or self.is_admin(request)
    
    def has_authenticated_or_read_access(self, request):
        """Check if user is authenticated or request is read-only."""
        return self.is_authenticated(request) or self.is_read_only_request(request)
