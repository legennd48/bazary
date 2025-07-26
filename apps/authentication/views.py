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
from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, ProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class RegisterView(APIView):
    """
    Register a new user.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        request_body=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: 'Bad Request'
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
    Get or update user profile.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(responses={200: ProfileSerializer})
    def get(self, request):
        """Get current user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer}
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
    
    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
