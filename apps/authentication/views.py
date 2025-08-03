"""
Authentication views.
"""

from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.core.swagger_docs import (
    SwaggerTags,
    SwaggerResponses,
    SwaggerExamples,
    get_testing_instructions_response,
    get_example_or_fallback,
)
from apps.core.capture_decorator import capture_for_swagger
from apps.core.permissions import (
    UserManagementPermission,
    ProfilePermission,
    PasswordChangePermission,
)
from apps.core.throttling.decorators import login_ratelimit, registration_ratelimit
from .models import User
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    """
    ## User Registration

    Register a new user account with email and password.

    ### 📝 Registration Process
    - Email validation and uniqueness check
    - Strong password requirements
    - Username validation
    - Automatic user creation

    ### 🔐 Security Features
    - Password hashing using Django's built-in system
    - Email format validation
    - Duplicate email prevention
    - Input sanitization
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Register New User",
        operation_description="""
        Register a new user account.
        
        ### Required Fields:
        - **email**: Valid email address (unique)
        - **username**: Unique username
        - **password**: Strong password (min 8 characters)
        - **password_confirm**: Password confirmation (must match password)
        
        ### Optional Fields:
        - **first_name**: User's first name
        - **last_name**: User's last name
        - **phone_number**: User's phone number
        
        ### Response:
        Returns user data (excluding password) upon successful registration.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="User email address",
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Unique username"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Strong password (min 8 characters)",
                ),
                "password_confirm": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Password confirmation (must match password)",
                ),
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="First name"
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Last name"
                ),
                "phone_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Phone number"
                ),
            },
            required=["email", "username", "password", "password_confirm"],
            example=SwaggerExamples.REGISTER_EXAMPLE,
        ),
        responses={
            201: openapi.Response(
                "User registered successfully",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_register",
                        "POST",
                        201,
                        {
                            "message": "User registered successfully",
                            "user": {
                                "id": "user-uuid",
                                "email": "user@example.com",
                                "username": "newuser",
                                "first_name": "John",
                                "last_name": "Doe",
                            },
                        },
                    )
                },
            ),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_register",
                        "POST",
                        400,
                        {
                            "email": ["This email is already registered."],
                            "password": [
                                "Password must be at least 8 characters long."
                            ],
                        },
                    )
                },
            ),
        },
    )
    @capture_for_swagger("auth_register")
    @registration_ratelimit(rate="3/h")
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response(
                {
                    "message": "User registered successfully",
                    "user": user_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    ## User Profile Management

    Manage the current user's profile information.

    ### 👤 Features
    - **Get Profile**: View current user information
    - **Update Profile**: Modify profile fields
    - **Secure Access**: Authentication required
    - **Privacy**: Users can only access their own profile

    ### 🔐 Security
    - JWT authentication required
    - User can only view/edit their own profile
    - Password updates handled separately
    """

    permission_classes = [ProfilePermission]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get User Profile",
        operation_description="""
        Retrieve the current authenticated user's profile information.
        
        ### Authentication Required
        Requires valid JWT access token in Authorization header.
        
        ### Response Data
        Returns user profile information excluding sensitive data like password.
        """,
        responses={
            200: openapi.Response(
                "Profile retrieved successfully",
                ProfileSerializer,
                examples={
                    "application/json": {
                        "id": "user-uuid",
                        "email": "user@example.com",
                        "username": "user123",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_joined": "2025-01-01T12:00:00Z",
                        "is_active": True,
                    }
                },
            ),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    def get(self, request):
        """Get current user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Update User Profile",
        operation_description="""
        Update the current authenticated user's profile information.
        
        ### Updatable Fields
        - **first_name**: First name
        - **last_name**: Last name  
        - **username**: Username (must be unique)
        
        ### Note
        Email and password updates require separate endpoints for security.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "first_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="First name"
                ),
                "last_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Last name"
                ),
                "username": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Username (must be unique)"
                ),
            },
            example={
                "first_name": "John",
                "last_name": "Smith",
                "username": "johnsmith",
            },
        ),
        responses={
            200: openapi.Response("Profile updated successfully", ProfileSerializer),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": {
                        "username": ["A user with that username already exists."]
                    }
                },
            ),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    def put(self, request):
        """Update current user profile."""
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (admin only).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserManagementPermission]

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[PasswordChangePermission],
        serializer_class=ChangePasswordSerializer,
    )
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()

        # Users can only change their own password unless they're admin
        if user != request.user and not request.user.is_staff:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"message": "Password changed successfully"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get Current User",
        operation_description="Get the current authenticated user's profile (shortcut endpoint)",
        responses={
            200: openapi.Response("Current user profile", ProfileSerializer),
            401: openapi.Response("Unauthorized - Valid token required"),
        },
    )
    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get Authentication Testing Instructions",
        operation_description="""
        Retrieve comprehensive testing instructions for the Authentication API.
        
        ### What's Included:
        - User registration testing
        - Login and token management
        - Profile management testing
        - Security testing scenarios
        - Example curl commands
        """,
        responses={200: get_testing_instructions_response("authentication")},
    )
    @action(detail=False, methods=["get"], url_path="testing-instructions")
    def testing_instructions(self, request):
        """Get comprehensive testing instructions for Authentication API."""
        from apps.core.swagger_docs import TestingInstructions

        return Response(
            {
                "title": "Authentication API Testing Instructions",
                "instructions": TestingInstructions.AUTHENTICATION_TESTING,
                "format": "markdown",
                "last_updated": "2025-01-28",
            }
        )


# Custom JWT Views with Swagger Documentation
class CustomTokenObtainPairView(TokenObtainPairView):
    @swagger_auto_schema(
        operation_summary="User login with JWT tokens",
        operation_description="""
        Authenticate user and obtain JWT access and refresh tokens.
        
        **Testing Steps:**
        1. Use email and password of an existing user account
        2. Submit login credentials
        3. Receive access token (valid for 60 minutes) and refresh token (valid for 1 day)
        4. Use access token in Authorization header: `Bearer <access_token>`
        5. Use refresh token to get new access tokens when expired
        
        **Success Response:** Access token and refresh token
        **Error Response:** Invalid credentials error
        """,
        tags=[SwaggerTags.AUTHENTICATION],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_EMAIL,
                    description="Email address of registered user",
                    example="user@example.com",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="User password",
                    example="userpassword123",
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="Login successful - JWT tokens returned",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_login",
                        "POST",
                        200,
                        {
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        },
                    )
                },
            ),
            401: openapi.Response(
                description="Invalid credentials",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_login",
                        "POST",
                        401,
                        {
                            "detail": "No active account found with the given credentials"
                        },
                    )
                },
            ),
        },
    )
    @capture_for_swagger("auth_login")
    @login_ratelimit(rate="5/m")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_summary="Refresh JWT access token",
        operation_description="""
        Use refresh token to obtain a new access token when the current one expires.
        
        **Testing Steps:**
        1. Use the refresh token obtained from login
        2. Submit refresh token to get new access token
        3. New access token is valid for another 60 minutes
        4. Continue using new access token for authenticated requests
        
        **Success Response:** New access token
        **Error Response:** Invalid or expired refresh token
        """,
        tags=[SwaggerTags.AUTHENTICATION],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Valid refresh token from login",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Token refresh successful",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_token_refresh",
                        "POST",
                        200,
                        {"access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                    )
                },
            ),
            401: openapi.Response(
                description="Invalid or expired refresh token",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_token_refresh",
                        "POST",
                        401,
                        {
                            "detail": "Token is invalid or expired",
                            "code": "token_not_valid",
                        },
                    )
                },
            ),
        },
    )
    @capture_for_swagger("auth_token_refresh")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    @swagger_auto_schema(
        operation_summary="Verify JWT token validity",
        operation_description="""
        Verify if a JWT token is valid and not expired.
        
        **Testing Steps:**
        1. Use an access token from login or refresh
        2. Submit token for verification
        3. Check if token is valid and active
        4. Use for debugging authentication issues
        
        **Success Response:** Empty response (200 status means token is valid)
        **Error Response:** Token validation error details
        """,
        tags=[SwaggerTags.AUTHENTICATION],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["token"],
            properties={
                "token": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="JWT token to verify",
                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Token is valid",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_token_verify", "POST", 200, {}
                    )
                },
            ),
            401: openapi.Response(
                description="Token is invalid or expired",
                examples={
                    "application/json": get_example_or_fallback(
                        "auth_token_verify",
                        "POST",
                        401,
                        {
                            "detail": "Token is invalid or expired",
                            "code": "token_not_valid",
                        },
                    )
                },
            ),
        },
    )
    @capture_for_swagger("auth_token_verify")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
