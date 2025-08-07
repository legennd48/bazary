"""
Enhanced authentication views package.
"""

from .admin import AdminUserManagementViewSet

# Import enhanced views
from .enhanced import (
    EmailVerificationView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ResendVerificationView,
)

# Import original views
from .original import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    ProfileView,
    RegisterView,
    UserViewSet,
)
from .profile import (
    EnhancedProfileView,
    UserActivityView,
    UserAddressViewSet,
)

__all__ = [
    # Original views
    "RegisterView",
    "ProfileView",
    "UserViewSet",
    "CustomTokenObtainPairView",
    "CustomTokenRefreshView",
    "CustomTokenVerifyView",
    # Enhanced views
    "EmailVerificationView",
    "ResendVerificationView",
    "PasswordResetRequestView",
    "PasswordResetConfirmView",
    "AdminUserManagementViewSet",
    "EnhancedProfileView",
    "UserAddressViewSet",
    "UserActivityView",
]
