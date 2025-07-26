"""
Products views.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Product, Tag
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductSearchSerializer,
    TagSerializer
)
from .filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product management.
    
    Provides CRUD operations for products with advanced filtering,
    search, and sorting capabilities.
    """
    queryset = Product.objects.select_related('category', 'created_by').prefetch_related('tags', 'images')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve', 'search', 'featured']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'search':
            return ProductSearchSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on permissions."""
        queryset = self.queryset
        
        # For non-admin users, only show active products
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'q', openapi.IN_QUERY,
                description="Search query",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category', openapi.IN_QUERY,
                description="Category ID",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: ProductSearchSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced product search."""
        queryset = self.get_queryset()
        
        # Text search
        query = request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        # Category filter
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Price range filter
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: ProductListSerializer(many=True)},
        operation_description="Get featured products"
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products."""
        queryset = self.get_queryset().filter(is_featured=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='get',
        responses={200: ProductListSerializer(many=True)},
        operation_description="Get products that are in stock"
    )
    @action(detail=False, methods=['get'])
    def in_stock(self, request):
        """Get products that are in stock."""
        queryset = self.get_queryset().filter(
            Q(track_inventory=False) | Q(stock_quantity__gt=0)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @swagger_auto_schema(
        method='post',
        responses={200: openapi.Response('Stock updated successfully')},
        operation_description="Update product stock"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def update_stock(self, request, pk=None):
        """Update product stock quantity."""
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response(
                {'error': 'Quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {'error': 'Quantity must be a non-negative integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.stock_quantity = quantity
        product.save()
        
        return Response({
            'message': 'Stock updated successfully',
            'product_id': product.id,
            'new_quantity': quantity,
            'is_in_stock': product.is_in_stock,
            'is_low_stock': product.is_low_stock
        })


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tag management.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
