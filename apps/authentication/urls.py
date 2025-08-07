"""
Authentication app URLs.
"""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

# Import from views package
from .views import (
    AdminUserManagementViewSet,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    EmailVerificationView,
    EnhancedProfileView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
    UserActivityView,
    UserAddressViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("admin/users", AdminUserManagementViewSet, basename="admin-user")
router.register("addresses", UserAddressViewSet, basename="address")

urlpatterns = [
    # JWT Token endpoints with Swagger documentation
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CustomTokenVerifyView.as_view(), name="token_verify"),
    # User management
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    # Enhanced profile management
    path("profile/enhanced/", EnhancedProfileView.as_view(), name="enhanced_profile"),
    path("activity/", UserActivityView.as_view(), name="user_activity"),
    # Email verification
    path("verify-email/", EmailVerificationView.as_view(), name="verify_email"),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    # Password reset
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password_reset_request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # User CRUD via router
    path("", include(router.urls)),
]
