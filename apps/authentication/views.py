"""
Authentication views.
"""

from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.core.swagger_docs import (
    SwaggerTags, SwaggerResponses, SwaggerExamples, 
    get_testing_instructions_response
)
from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    ChangePasswordSerializer
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
        
        ### Optional Fields:
        - **first_name**: User's first name
        - **last_name**: User's last name
        
        ### Response:
        Returns user data (excluding password) upon successful registration.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='User email address'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Unique username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Strong password (min 8 characters)'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
            },
            required=['email', 'username', 'password'],
            example=SwaggerExamples.REGISTER_EXAMPLE
        ),
        responses={
            201: openapi.Response(
                "User registered successfully",
                examples={
                    "application/json": {
                        "message": "User registered successfully",
                        "user": {
                            "id": "user-uuid",
                            "email": "user@example.com",
                            "username": "newuser",
                            "first_name": "John",
                            "last_name": "Doe"
                        }
                    }
                }
            ),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": {
                        "email": ["This email is already registered."],
                        "password": ["Password must be at least 8 characters long."]
                    }
                }
            )
        }
    )
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_serializer = UserSerializer(user)
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': user_serializer.data
                },
                status=status.HTTP_201_CREATED
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
    permission_classes = [IsAuthenticated]
    
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
                        "is_active": True
                    }
                }
            ),
            401: openapi.Response("Unauthorized - Valid token required")
        }
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
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username (must be unique)'),
            },
            example={
                "first_name": "John",
                "last_name": "Smith",
                "username": "johnsmith"
            }
        ),
        responses={
            200: openapi.Response(
                "Profile updated successfully",
                ProfileSerializer
            ),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": {
                        "username": ["A user with that username already exists."]
                    }
                }
            ),
            401: openapi.Response("Unauthorized - Valid token required")
        }
    )
    def put(self, request):
        """Update current user profile."""
        serializer = ProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
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
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        serializer_class=ChangePasswordSerializer
    )
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        
        # Users can only change their own password unless they're admin
        if user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Get Current User",
        operation_description="Get the current authenticated user's profile (shortcut endpoint)",
        responses={
            200: openapi.Response("Current user profile", ProfileSerializer),
            401: openapi.Response("Unauthorized - Valid token required")
        }
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
        responses={
            200: get_testing_instructions_response('authentication')
        }
    )
    @action(detail=False, methods=['get'], url_path='testing-instructions')
    def testing_instructions(self, request):
        """Get comprehensive testing instructions for Authentication API."""
        from apps.core.swagger_docs import TestingInstructions
        
        return Response({
            'title': 'Authentication API Testing Instructions',
            'instructions': TestingInstructions.AUTHENTICATION_TESTING,
            'format': 'markdown',
            'last_updated': '2025-01-28'
        })
