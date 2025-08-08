"""
Original authentication views.
"""

from django.contrib.auth import get_user_model

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.core.permissions import (
    PasswordChangePermission,
    ProfilePermission,
    UserManagementPermission,
)
from apps.core.swagger_docs import SwaggerTags

from ..models import User
from ..serializers import (
    ChangePasswordSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    """
    ## User Registration

    Register a new user account with email verification.

    ### 📝 Registration Process
    - **Account Creation**: Creates new user account with provided details
    - **Email Verification**: Sends verification email to confirm account
    - **Password Security**: Validates password strength and confirmation
    - **Unique Validation**: Ensures username and email are unique

    ### 🔐 Security Features
    - Password strength validation
    - Email format validation
    - Duplicate account prevention
    - Automatic email verification token generation
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Register New User",
        operation_description="""
        Create a new user account with email verification.
        
        ### Required Fields:
        - **username**: Unique username (3-150 characters)
        - **email**: Valid email address (will receive verification email)
        - **password**: Secure password (min 8 characters)
        - **password_confirm**: Must match password field
        - **first_name**: User's first name
        - **last_name**: User's last name
        
        ### Optional Fields:
        - **phone_number**: Contact phone number
        
        ### Response:
        - Returns user data and success message
        - Sends email verification to provided email address
        - User account will be created but requires email verification
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                "username",
                "email",
                "password",
                "password_confirm",
                "first_name",
                "last_name",
            ],
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Unique username (3-150 characters)",
                    example="john_doe",
                ),
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Valid email address for account verification",
                    example="john.doe@example.com",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Secure password (minimum 8 characters)",
                    example="SecurePass123!",
                ),
                "password_confirm": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Confirm password (must match password)",
                    example="SecurePass123!",
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's first name",
                    example="John",
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's last name",
                    example="Doe",
                ),
                "phone_number": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Contact phone number (optional)",
                    example="+1234567890",
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="User registered successfully",
                        ),
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(
                                    type=openapi.TYPE_INTEGER, example=1
                                ),
                                "email": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="john.doe@example.com",
                                ),
                                "first_name": openapi.Schema(
                                    type=openapi.TYPE_STRING, example="John"
                                ),
                                "last_name": openapi.Schema(
                                    type=openapi.TYPE_STRING, example="Doe"
                                ),
                                "date_joined": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_DATETIME,
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="Validation error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "username": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["A user with that username already exists."],
                        ),
                        "email": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Enter a valid email address."],
                        ),
                        "password": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=[
                                "This password is too short. It must contain at least 8 characters."
                            ],
                        ),
                        "non_field_errors": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Passwords don't match."],
                        ),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Return minimal user data for security
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined,
            }
            return Response(
                {"message": "User registered successfully", "user": user_data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """User Profile Management API view."""

    permission_classes = [ProfilePermission]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Profile",
        operation_description="""
        Retrieve the current user's profile information.
        
        ### Response Includes:
        - Basic user information (name, email, username)
        - Profile completion status
        - Account security information
        """,
        responses={
            200: openapi.Response("User profile data", ProfileSerializer),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    def get(self, request):
        """Retrieve user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Update User Profile (Full)",
        operation_description="""
        Update user profile with complete data replacement.
        
        ### Note:
        This is a full update (PUT) - all fields should be provided.
        For partial updates, use PATCH method instead.
        """,
        request_body=ProfileSerializer,
        responses={
            200: openapi.Response("Profile updated successfully", ProfileSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    def put(self, request):
        """Update user profile (full update)."""
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Update User Profile (Partial)",
        operation_description="""
        Update user profile with partial data.
        
        ### Note:
        This is a partial update (PATCH) - only provide fields to be updated.
        All fields are optional.
        """,
        request_body=ProfileSerializer,
        responses={
            200: openapi.Response("Profile updated successfully", ProfileSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    def patch(self, request):
        """Update user profile (partial update)."""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management (admin only)."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserManagementPermission]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        # Handle Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Change User Password",
        operation_description="""
        Change password for a specific user (admin only).
        
        ### Security:
        - Requires admin/staff permissions
        - Password strength validation applied
        - Old password verification required
        - Activity logging for security audit
        """,
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Password changed successfully",
                        )
                    },
                ),
            ),
            400: openapi.Response("Validation error"),
            403: openapi.Response("Admin access required"),
        },
    )
    @action(
        detail=True, methods=["post"], permission_classes=[PasswordChangePermission]
    )
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data, context={"user": user})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view."""

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Login User",
        operation_description="""
        Authenticate user and obtain JWT access and refresh tokens.
        
        ### Authentication:
        - Provide username/email and password
        - Returns access token (expires in 15 minutes)
        - Returns refresh token (expires in 7 days)
        
        ### Token Usage:
        - Use access token in Authorization header: `Bearer <access_token>`
        - Use refresh token to get new access tokens when expired
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["username", "password"],
            properties={
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Username or email address",
                    example="john_doe",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="User password",
                    example="SecurePass123!",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT access token (expires in 15 minutes)",
                            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        ),
                        "refresh": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="JWT refresh token (expires in 7 days)",
                            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="No active account found with the given credentials",
                        )
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Obtain JWT token pair."""
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    """Custom JWT token refresh view."""

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Refresh Access Token",
        operation_description="""
        Refresh an expired access token using a valid refresh token.
        
        ### Process:
        - Provide valid refresh token
        - Receive new access token
        - Refresh token remains valid until its expiry
        
        ### Security:
        - Refresh tokens are long-lived (7 days)
        - Access tokens are short-lived (15 minutes)
        - Use this endpoint to maintain authentication
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Valid JWT refresh token",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="New JWT access token",
                            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="Invalid or expired refresh token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Token is invalid or expired",
                        ),
                        "code": openapi.Schema(
                            type=openapi.TYPE_STRING, example="token_not_valid"
                        ),
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Refresh access token."""
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    """Custom JWT token verify view."""

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Verify Token",
        operation_description="""
        Verify if a JWT token is valid and not expired.
        
        ### Usage:
        - Check token validity before making authenticated requests
        - Useful for client-side token validation
        - Works with both access and refresh tokens
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="JWT token to verify (access or refresh)",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Token is valid",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={},  # Empty response for valid token
                ),
            ),
            401: openapi.Response(
                description="Invalid or expired token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Token is invalid or expired",
                        ),
                        "code": openapi.Schema(
                            type=openapi.TYPE_STRING, example="token_not_valid"
                        ),
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        """Verify token."""
        return super().post(request, *args, **kwargs)
