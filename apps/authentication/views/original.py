"""
Original authentication views.
"""

from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema, inline_serializer
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
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
        operation_summary="Register New User Account",
        operation_description="""
        ## 🔐 User Registration Endpoint
        
        Create a new user account with comprehensive validation and email verification.
        
        ### 📋 Process Flow:
        1. **Account Creation**: Validates and creates new user account
        2. **Email Verification**: Automatically sends verification email
        3. **Security Validation**: Ensures password strength and uniqueness
        4. **Response**: Returns user data and success confirmation
        
        ### 🔑 Required Fields:
        - **username**: Unique identifier (3-150 characters, alphanumeric + underscore)
        - **email**: Valid email address (receives verification email)
        - **password**: Secure password (minimum 8 characters with complexity rules)
        - **password_confirm**: Must exactly match password field
        - **first_name**: User's first name (required for personalization)
        - **last_name**: User's last name (required for personalization)
        
        ### 📱 Optional Fields:
        - **phone_number**: Contact phone number (international format recommended)
        
        ### ✅ Success Response:
        - User account created successfully
        - Email verification sent to provided address
        - Account requires email verification before full activation
        - Returns user data with verification status
        
        ### ⚠️ Validation Rules:
        - Username must be unique across all users
        - Email must be valid and unique
        - Password must meet security requirements
        - All required fields must be provided
        
        ### 🔄 Next Steps:
        After registration, users should:
        1. Check email for verification link
        2. Click verification link or use `/verify-email/` endpoint
        3. Use `/token/` endpoint to login after verification
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
    """
    ## User Management API

    Basic user management for administrative operations.

    ### 👥 Features
    - **User List**: Get all users (admin only)
    - **User Details**: View specific user information
    - **User Updates**: Modify user accounts
    - **User Creation**: Create new user accounts

    ### 🔐 Permissions
    - **Admin Access**: Full CRUD operations for all users
    - **Self Access**: Users can view/update their own profile only
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserManagementPermission]

    def get_queryset(self):
        """Filter queryset based to user permissions."""
        # Handle Swagger schema generation
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="List Users",
        operation_description="Get a list of all users (Admin only)",
        responses={
            200: openapi.Response(
                "Users retrieved successfully", UserSerializer(many=True)
            ),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
        },
    )
    def list(self, request, *args, **kwargs):
        """List all users."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Get User Details",
        operation_description="Retrieve detailed information about a specific user (Admin only)",
        responses={
            200: openapi.Response(
                "User details retrieved successfully", UserSerializer
            ),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
            404: openapi.Response("User not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed user information."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Create User",
        operation_description="Create a new user account (Admin only)",
        request_body=UserSerializer,
        responses={
            201: openapi.Response("User created successfully", UserSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create a new user."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Update User",
        operation_description="Update an existing user account (Admin only)",
        request_body=UserSerializer,
        responses={
            200: openapi.Response("User updated successfully", UserSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
            404: openapi.Response("User not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        """Update a user."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Partial Update User",
        operation_description="Partially update an existing user account (Admin only)",
        request_body=UserSerializer,
        responses={
            200: openapi.Response("User updated successfully", UserSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
            404: openapi.Response("User not found"),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a user."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.ADMIN_USER_MANAGEMENT],
        operation_summary="Delete User",
        operation_description="Delete an existing user account (Admin only)",
        responses={
            204: openapi.Response("User deleted successfully"),
            401: openapi.Response("Unauthorized - Admin access required"),
            403: openapi.Response("Forbidden - Staff privileges required"),
            404: openapi.Response("User not found"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a user."""
        return super().destroy(request, *args, **kwargs)

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
    """
    ## JWT Token Authentication

    Secure user authentication with JWT token generation.

    ### 🔐 Authentication Process
    - **Credential Validation**: Verifies username/email and password
    - **Token Generation**: Creates access and refresh tokens
    - **Session Management**: Enables stateless authentication
    - **Security**: JWT tokens with configurable expiration
    """

    @extend_schema(
        request=inline_serializer(
            name="TokenObtainPairRequest",
            fields={
                "email": drf_serializers.EmailField(),
                "password": drf_serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                name="TokenPairResponse",
                fields={
                    "access": drf_serializers.CharField(),
                    "refresh": drf_serializers.CharField(),
                },
            )
        },
        tags=[SwaggerTags.AUTHENTICATION],
        summary="🔑 User Login & Token Generation",
        description="Authenticate with email & password to obtain JWT tokens.",
    )
    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="🔑 User Login & Token Generation",
        operation_description="""
        ## 🔐 Authenticate User and Obtain JWT Tokens
        
        Primary authentication endpoint for user login and token generation.
        
        ### 📋 Process Flow:
        1. **Credential Validation**: Verifies username/email and password
        2. **Account Verification**: Checks if email is verified (if required)
        3. **Token Generation**: Creates JWT access and refresh tokens
        4. **User Data**: Returns authenticated user information
        
        ### 🎫 Token Information:
        - **Access Token**: Short-lived (15 minutes) for API requests
        - **Refresh Token**: Long-lived (7 days) for generating new access tokens
        - **Token Type**: Bearer tokens for Authorization header
        
    ### 📱 Accepted Credentials:
    - **Email**: Your registered email address (used as the username field)
    - **Password**: Your account password
        
        ### 🔧 Usage Instructions:
        ```bash
        # Use access token in API requests:
        curl -H "Authorization: Bearer <access_token>" /api/v1/auth/profile/
        
        # Refresh tokens when expired:
        curl -X POST /api/v1/auth/token/refresh/ -d '{"refresh": "<refresh_token>"}'
        ```
        
        ### ⚠️ Security Notes:
        - Store tokens securely (not in localStorage for web apps)
        - Use HTTPS in production
        - Refresh tokens before access token expires
        - Logout destroys refresh tokens server-side
        
        ### 🔄 Next Steps:
        After login:
        1. Store both tokens securely
        2. Use access token for authenticated requests
        3. Set up automatic token refresh
        4. Access user profile at `/profile/` endpoint
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Email address used to log in",
                    example="john.doe@example.com",
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
    """
    ## JWT Token Refresh

    Maintain authentication by refreshing expired access tokens.

    ### 🔄 Token Refresh Process
    - **Validation**: Verifies refresh token validity
    - **Generation**: Creates new access token
    - **Persistence**: Keeps refresh token valid until expiry
    - **Security**: Maintains session without re-authentication
    """

    @swagger_auto_schema(
        tags=[SwaggerTags.TOKEN_MANAGEMENT],
        operation_summary="🔄 Refresh Access Token",
        operation_description="""
        ## 🎫 Generate New Access Token from Refresh Token
        
        Essential endpoint for maintaining long-term authentication sessions.
        
        ### 📋 Process Flow:
        1. **Token Validation**: Verifies refresh token is valid and not expired
        2. **Access Generation**: Creates new access token with fresh expiration
        3. **Session Continuity**: Maintains user session without re-login
        4. **Security Check**: Validates token hasn't been blacklisted
        
        ### 🕐 Token Lifecycle:
        - **Access Token**: Expires every 15 minutes (short-lived for security)
        - **Refresh Token**: Expires every 7 days (long-lived for convenience)
        - **Auto-Refresh**: Implement client-side auto-refresh before expiry
        
        ### 🔧 Implementation Pattern:
        ```javascript
        // Client-side auto-refresh example
        const refreshToken = async () => {
          const response = await fetch('/api/v1/auth/token/refresh/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh: localStorage.getItem('refresh_token')})
          });
          const data = await response.json();
          localStorage.setItem('access_token', data.access);
        };
        
        // Set up auto-refresh 1 minute before expiry
        setTimeout(refreshToken, 14 * 60 * 1000); // 14 minutes
        ```
        
        ### ⚠️ Security Best Practices:
        - Implement token refresh in background
        - Handle refresh token expiry gracefully
        - Clear tokens on logout
        - Use secure storage for tokens
        
        ### 🚨 Error Handling:
        - **401 Unauthorized**: Refresh token expired or invalid
        - **400 Bad Request**: Malformed token or request
        - **Token Blacklisted**: User logged out or security breach
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
    """
    ## JWT Token Verification

    Validate JWT tokens without requiring refresh.

    ### 🔍 Verification Process
    - **Token Validation**: Checks token format and signature
    - **Expiry Check**: Verifies token hasn't expired
    - **Blacklist Check**: Ensures token hasn't been revoked
    - **Performance**: Fast validation for client-side checks
    """

    @swagger_auto_schema(
        tags=[SwaggerTags.TOKEN_MANAGEMENT],
        operation_summary="🔍 Verify Token Validity",
        operation_description="""
        ## 🎫 Validate JWT Token Without Refresh
        
        Quick token validation endpoint for client-side authentication checks.
        
        ### 📋 Verification Process:
        1. **Format Check**: Validates JWT structure and format
        2. **Signature Verification**: Confirms token authenticity
        3. **Expiry Validation**: Checks if token is still valid
        4. **Blacklist Check**: Ensures token hasn't been revoked
        
        ### 🎯 Use Cases:
        - **Client-side Validation**: Check token before API calls
        - **Session Monitoring**: Periodic token health checks
        - **Security Audits**: Validate token integrity
        - **Pre-request Checks**: Avoid failed API calls
        
        ### 🔧 Implementation Examples:
        ```javascript
        // Client-side token validation
        const isTokenValid = async (token) => {
          try {
            const response = await fetch('/api/v1/auth/token/verify/', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({token})
            });
            return response.ok; // true if valid, false if invalid
          } catch (error) {
            return false;
          }
        };
        
        // Check before making authenticated requests
        if (await isTokenValid(accessToken)) {
          // Proceed with API call
          makeAuthenticatedRequest();
        } else {
          // Refresh token or redirect to login
          refreshTokenOrLogin();
        }
        ```
        
        ### ⚡ Performance Benefits:
        - **Fast Validation**: No database queries for basic checks
        - **Network Efficient**: Small request/response payload
        - **Client Optimization**: Reduce failed API calls
        - **Security Layer**: Additional token validation
        
        ### 🎭 Token Types Supported:
        - **Access Tokens**: Short-lived authentication tokens
        - **Refresh Tokens**: Long-lived refresh tokens
        - **Custom Tokens**: Any JWT token issued by this system
        
        ### 📊 Response Patterns:
        - **200 OK**: Token is valid and active
        - **401 Unauthorized**: Token is invalid, expired, or blacklisted
        - **400 Bad Request**: Malformed token or request
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
