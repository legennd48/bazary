"""
Categories views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.core.swagger_docs import (
    SwaggerTags, SwaggerResponses, SwaggerExamples
)
from .models import Category
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, CategoryCreateSerializer
)


@swagger_auto_schema(
    tags=[SwaggerTags.CATEGORIES],
    operation_description="Category management endpoints for organizing products hierarchically."
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ## Category Management API
    
    Hierarchical category system for organizing products.
    
    ### 🗂️ Core Operations
    - **List Categories**: Get all categories with filtering
    - **Category Details**: Get detailed category information
    - **Create Category**: Add new categories (Admin only)
    - **Update Category**: Modify existing categories (Admin only)
    - **Delete Category**: Remove categories (Admin only)
    
    ### 🌳 Hierarchical Features
    - **Parent-Child Structure**: Support for nested categories
    - **Tree View**: Get categories in tree structure
    - **Root Categories**: Get top-level categories
    - **Subcategories**: Get child categories
    
    ### 🔍 Advanced Features
    - **Search**: Search categories by name and description
    - **Filtering**: Filter by parent, active status
    - **Sorting**: Sort by name, sort order, creation date
    - **Product Integration**: Get products within categories
    
    ### 🔐 Permissions
    - **Public Access**: List, detail, tree, and product views
    - **Admin Only**: Create, update, delete operations
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve', 'tree']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action == 'tree':
            return CategoryTreeSerializer
        return CategorySerializer
    
    def get_queryset(self):
        """Filter queryset based on action and permissions."""
        queryset = Category.objects.all()
        
        # For non-admin users, only show active categories
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @swagger_auto_schema(
        method='get',
        responses={200: CategoryTreeSerializer(many=True)},
        operation_description="Get categories in tree structure"
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get categories in tree structure."""
        categories = self.get_queryset().filter(parent=None)
        serializer = CategoryTreeSerializer(categories, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: CategorySerializer(many=True)},
        operation_description="Get root categories (no parent)"
    )
    @action(detail=False, methods=['get'])
    def roots(self, request):
        """Get root categories (categories without parent)."""
        categories = self.get_queryset().filter(parent=None)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: CategorySerializer(many=True)},
        operation_description="Get subcategories of a specific category"
    )
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get subcategories of a specific category."""
        category = self.get_object()
        subcategories = category.subcategories.filter(is_active=True)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: openapi.Response('Products in category', examples={
            'application/json': {
                'count': 10,
                'products': []
            }
        })},
        operation_description="Get products in a specific category"
    )
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in a specific category."""
        category = self.get_object()
        products = category.products.filter(is_active=True)
        
        # Import here to avoid circular imports
        from apps.products.serializers import ProductListSerializer
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response({
            'count': products.count(),
            'category': self.get_serializer(category).data,
            'products': serializer.data
        })
