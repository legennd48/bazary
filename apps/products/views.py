"""
Products views.

This module imports all product-related views from the views package.
"""

from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrReadOnly
from apps.core.permissions.product import (
    ProductBulkOperationPermission,
    ProductPermission,
)
from apps.core.swagger_docs import (
    SwaggerExamples,
    SwaggerParameters,
    SwaggerResponses,
    SwaggerTags,
    get_testing_instructions_response,
)
from apps.core.throttling.decorators import RateLimitMixin, search_ratelimit

from .filters import ProductFilter
from .models import Product, Tag
from .serializers import (
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductSearchSerializer,
    TagSerializer,
)

# Import all views from the views package
from .views import *  # noqa: F401,F403


@swagger_auto_schema(
    tags=[SwaggerTags.PRODUCTS],
    operation_description="Product management endpoints with CRUD operations, filtering, and search capabilities.",
)
class ProductViewSet(RateLimitMixin, viewsets.ModelViewSet):
    """
    ## Product Management API

    Comprehensive product management system with the following features:

    ### 🛍️ Core Operations
    - **List Products**: Get paginated list of products with filtering
    - **Product Details**: Get detailed information about a specific product
    - **Create Product**: Add new products (Admin only)
    - **Update Product**: Modify existing products (Admin only)
    - **Delete Product**: Remove products (Admin only)

    ### 🔍 Advanced Features
    - **Search**: Multi-field text search across name, description, and SKU
    - **Filtering**: Filter by category, price range, stock status, featured status
    - **Sorting**: Sort by name, price, creation date, stock quantity
    - **Pagination**: Efficient handling of large product catalogs

    ### 🎯 Special Endpoints
    - **Featured Products**: Get products marked as featured
    - **Stock Management**: Update product inventory levels
    - **In-Stock Products**: Get only products currently in stock

    ### 🔐 Permissions
    - **Public Access**: List, detail, search, featured products
    - **Admin Only**: Create, update, delete, stock management

    ### 📊 Performance
    - Optimized queries with select_related and prefetch_related
    - Database indexes for efficient filtering and searching
    - Pagination to handle large datasets
    """

    queryset = Product.objects.select_related(
        "category", "created_by"
    ).prefetch_related("tags", "images")
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "short_description", "sku"]
    ordering_fields = ["name", "price", "created_at", "stock_quantity"]
    ordering = ["-created_at"]

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="List Products",
        operation_description="Get a paginated list of products with optional filtering and search",
        manual_parameters=[
            SwaggerParameters.SEARCH_QUERY,
            SwaggerParameters.PAGE,
            SwaggerParameters.PAGE_SIZE,
            SwaggerParameters.ORDERING,
            SwaggerParameters.CATEGORY_FILTER,
            SwaggerParameters.PRICE_MIN,
            SwaggerParameters.PRICE_MAX,
            SwaggerParameters.IS_FEATURED,
            SwaggerParameters.IN_STOCK,
        ],
        responses={
            200: openapi.Response(
                "Products retrieved successfully",
                ProductListSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 150,
                        "next": "http://localhost:8000/api/v1/products/?page=2",
                        "previous": None,
                        "results": [SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE],
                    }
                },
            ),
            **SwaggerResponses.standard_crud(),
        },
    )
    def list(self, request, *args, **kwargs):
        """List products with filtering and pagination."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Product Details",
        operation_description="Retrieve detailed information about a specific product",
        responses={
            200: openapi.Response(
                "Product details retrieved successfully",
                ProductDetailSerializer,
                examples={"application/json": SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE},
            ),
            **SwaggerResponses.standard_crud(),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed product information."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Create Product",
        operation_description="Create a new product (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Product name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Detailed description"
                ),
                "short_description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Brief description"
                ),
                "price": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Product price"
                ),
                "category": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Category ID"
                ),
                "sku": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Stock Keeping Unit"
                ),
                "stock_quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Stock quantity"
                ),
                "track_inventory": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Enable inventory tracking"
                ),
                "is_featured": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Mark as featured"
                ),
                "is_active": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Product is active"
                ),
                "tags": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="Tag IDs",
                ),
            },
            required=["name", "description", "price", "category"],
            example=SwaggerExamples.PRODUCT_CREATE_EXAMPLE,
        ),
        responses={
            201: openapi.Response(
                "Product created successfully",
                ProductDetailSerializer,
                examples={"application/json": SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE},
            ),
            **SwaggerResponses.standard_crud(),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create a new product."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Update Product",
        operation_description="Update an existing product (Admin only)",
        request_body=ProductCreateUpdateSerializer,
        responses={
            200: openapi.Response(
                "Product updated successfully", ProductDetailSerializer
            ),
            **SwaggerResponses.standard_crud(),
        },
    )
    def update(self, request, *args, **kwargs):
        """Update a product."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Partial Update Product",
        operation_description="Partially update an existing product (Admin only)",
        request_body=ProductCreateUpdateSerializer,
        responses={
            200: openapi.Response(
                "Product updated successfully", ProductDetailSerializer
            ),
            **SwaggerResponses.standard_crud(),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a product."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Delete Product",
        operation_description="Delete an existing product (Admin only)",
        responses={
            204: openapi.Response("Product deleted successfully"),
            **SwaggerResponses.standard_crud(),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a product."""
        return super().destroy(request, *args, **kwargs)

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["list", "retrieve", "search", "featured", "in_stock"]:
            permission_classes = [ProductPermission]
        else:
            permission_classes = [ProductPermission]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        elif self.action == "search":
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
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Search Products",
        operation_description="""
        Advanced product search with multiple filters and text search.
        
        ### Search Features:
        - **Text Search**: Search across name, description, short_description, and SKU
        - **Category Filter**: Filter by specific category
        - **Price Range**: Filter by minimum and maximum price
        - **Pagination**: Results are paginated for performance
        
        ### Example Usage:
        - Basic search: `?q=headphones`
        - Category filter: `?category=1`
        - Price range: `?price_min=50&price_max=200`
        - Combined: `?q=wireless&category=1&price_min=100`
        """,
        manual_parameters=[
            SwaggerParameters.SEARCH_QUERY,
            SwaggerParameters.CATEGORY_FILTER,
            SwaggerParameters.PRICE_MIN,
            SwaggerParameters.PRICE_MAX,
            SwaggerParameters.PAGE,
            SwaggerParameters.PAGE_SIZE,
        ],
        responses={
            200: openapi.Response(
                "Search results",
                ProductSearchSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 25,
                        "next": None,
                        "previous": None,
                        "results": [SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE],
                    }
                },
            ),
            400: openapi.Response("Invalid search parameters"),
        },
    )
    @action(detail=False, methods=["get"])
    @search_ratelimit(rate="30/m")
    def search(self, request):
        """Advanced product search."""
        queryset = self.get_queryset()

        # Text search
        query = request.query_params.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(short_description__icontains=query)
                | Q(tags__name__icontains=query)
            ).distinct()

        # Category filter
        category_id = request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Price range filter
        price_min = request.query_params.get("price_min")
        price_max = request.query_params.get("price_max")
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
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Featured Products",
        operation_description="""
        Retrieve products that are marked as featured.
        
        ### Features:
        - Returns only products with `is_featured=True`
        - Includes pagination for performance
        - Public access - no authentication required
        - Optimized for homepage/promotional displays
        
        ### Use Cases:
        - Homepage product showcase
        - Promotional banners
        - Marketing campaigns
        - Special offers section
        """,
        manual_parameters=[
            SwaggerParameters.PAGE,
            SwaggerParameters.PAGE_SIZE,
        ],
        responses={
            200: openapi.Response(
                "Featured products retrieved successfully",
                ProductListSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 8,
                        "next": None,
                        "previous": None,
                        "results": [SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured products."""
        queryset = self.get_queryset().filter(is_featured=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get In-Stock Products",
        operation_description="""
        Retrieve products that are currently available in stock.
        
        ### Stock Logic:
        - Products with `track_inventory=False` (unlimited stock)
        - Products with `stock_quantity > 0`
        - Excludes out-of-stock items automatically
        
        ### Use Cases:
        - Display only available products
        - Inventory management
        - Customer shopping experience
        - Stock availability checks
        """,
        manual_parameters=[
            SwaggerParameters.PAGE,
            SwaggerParameters.PAGE_SIZE,
            SwaggerParameters.ORDERING,
        ],
        responses={
            200: openapi.Response(
                "In-stock products retrieved successfully",
                ProductListSerializer(many=True),
                examples={
                    "application/json": {
                        "count": 120,
                        "next": "http://localhost:8000/api/v1/products/in_stock/?page=2",
                        "previous": None,
                        "results": [SwaggerExamples.PRODUCT_RESPONSE_EXAMPLE],
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"])
    def in_stock(self, request):
        """Get products that are in stock."""
        queryset = self.get_queryset().filter(
            Q(track_inventory=False) | Q(stock_quantity__gt=0)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Update Product Stock",
        operation_description="""
        Update the stock quantity for a specific product (Admin only).
        
        ### Features:
        - Updates `stock_quantity` field
        - Validates quantity is non-negative integer
        - Returns updated stock status
        - Admin authentication required
        
        ### Stock Status Response:
        - `is_in_stock`: Whether product is available
        - `is_low_stock`: Whether stock is below threshold
        - `new_quantity`: Updated stock quantity
        
        ### Use Cases:
        - Inventory management
        - Stock replenishment
        - Manual stock adjustments
        - Bulk inventory updates
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "quantity": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="New stock quantity (must be non-negative)",
                    minimum=0,
                    example=25,
                )
            },
            required=["quantity"],
            example={"quantity": 25},
        ),
        responses={
            200: openapi.Response(
                "Stock updated successfully",
                examples={
                    "application/json": {
                        "message": "Stock updated successfully",
                        "product_id": 1,
                        "new_quantity": 25,
                        "is_in_stock": True,
                        "is_low_stock": False,
                    }
                },
            ),
            400: openapi.Response(
                "Invalid quantity",
                examples={
                    "application/json": {
                        "error": "Quantity must be a non-negative integer"
                    }
                },
            ),
            401: openapi.Response("Unauthorized - Admin access required"),
            404: openapi.Response("Product not found"),
        },
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[ProductBulkOperationPermission],
    )
    def update_stock(self, request, pk=None):
        """Update product stock quantity."""
        product = self.get_object()
        quantity = request.data.get("quantity")

        if quantity is None:
            return Response(
                {"error": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(quantity)
            if quantity < 0:
                raise ValueError()
        except (ValueError, TypeError):
            return Response(
                {"error": "Quantity must be a non-negative integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.stock_quantity = quantity
        product.save()

        return Response(
            {
                "message": "Stock updated successfully",
                "product_id": product.id,
                "new_quantity": quantity,
                "is_in_stock": product.is_in_stock,
                "is_low_stock": product.is_low_stock,
            }
        )

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Testing Instructions",
        operation_description="""
        Retrieve comprehensive testing instructions for the Products API.
        
        ### What's Included:
        - Step-by-step testing scenarios
        - Example curl commands
        - Expected responses
        - Error case testing
        - Performance testing guidelines
        
        ### Testing Categories:
        - **Basic CRUD Operations**
        - **Search and Filtering**
        - **Permission Testing**
        - **Error Handling**
        - **Performance Testing**
        """,
        responses={200: get_testing_instructions_response("products")},
    )
    @action(detail=False, methods=["get"], url_path="testing-instructions")
    def testing_instructions(self, request):
        """Get comprehensive testing instructions for Products API."""
        from apps.core.swagger_docs import TestingInstructions

        return Response(
            {
                "title": "Products API Testing Instructions",
                "instructions": TestingInstructions.PRODUCTS_TESTING,
                "format": "markdown",
                "last_updated": "2025-01-28",
            }
        )


@swagger_auto_schema(
    tags=[SwaggerTags.TAGS],
    operation_description="Tag management endpoints for organizing products.",
)
class TagViewSet(viewsets.ModelViewSet):
    """
    ## Tag Management API

    Simple tag system for organizing and categorizing products.

    ### 🏷️ Core Operations
    - **List Tags**: Get all available tags
    - **Tag Details**: Get information about a specific tag
    - **Create Tag**: Add new tags (Admin only)
    - **Update Tag**: Modify existing tags (Admin only)
    - **Delete Tag**: Remove tags (Admin only)

    ### 🔍 Features
    - **Search**: Search tags by name
    - **Sorting**: Sort by name or creation date
    - **Public Access**: Anyone can view tags
    - **Admin Management**: Only admins can modify tags

    ### 🔗 Product Integration
    - Tags can be assigned to multiple products
    - Products can have multiple tags
    - Used for filtering and categorization
    - Enhances search functionality

    ### 🔐 Permissions
    - **Public Access**: List and detail views
    - **Admin Only**: Create, update, delete operations
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    @swagger_auto_schema(
        tags=[SwaggerTags.TAGS],
        operation_summary="List Tags",
        operation_description="Get a list of all available tags with optional search and sorting",
        manual_parameters=[
            SwaggerParameters.SEARCH_QUERY,
            SwaggerParameters.ORDERING,
            SwaggerParameters.PAGE,
            SwaggerParameters.PAGE_SIZE,
        ],
        responses={
            200: openapi.Response(
                "Tags retrieved successfully",
                TagSerializer(many=True),
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "wireless",
                            "description": "Wireless technology products",
                        },
                        {
                            "id": 2,
                            "name": "premium",
                            "description": "Premium quality products",
                        },
                        {
                            "id": 3,
                            "name": "electronics",
                            "description": "Electronic devices",
                        },
                    ]
                },
            )
        },
    )
    def list(self, request, *args, **kwargs):
        """List all tags with optional search and sorting."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.TAGS],
        operation_summary="Get Tag Details",
        operation_description="Retrieve detailed information about a specific tag",
        responses={
            200: openapi.Response(
                "Tag details retrieved successfully",
                TagSerializer,
                examples={"application/json": SwaggerExamples.TAG_CREATE_EXAMPLE},
            ),
            404: openapi.Response("Tag not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """Get detailed tag information."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.TAGS],
        operation_summary="Create Tag",
        operation_description="Create a new tag (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Tag name"
                ),
                "description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Tag description"
                ),
            },
            required=["name"],
            example=SwaggerExamples.TAG_CREATE_EXAMPLE,
        ),
        responses={
            201: openapi.Response(
                "Tag created successfully",
                TagSerializer,
                examples={"application/json": SwaggerExamples.TAG_CREATE_EXAMPLE},
            ),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Admin access required"),
        },
    )
    def create(self, request, *args, **kwargs):
        """Create a new tag."""
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.TAGS],
        operation_summary="Update Tag",
        operation_description="Update an existing tag (Admin only)",
        request_body=TagSerializer,
        responses={
            200: openapi.Response("Tag updated successfully", TagSerializer),
            400: openapi.Response("Validation error"),
            401: openapi.Response("Unauthorized - Admin access required"),
            404: openapi.Response("Tag not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        """Update a tag."""
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.TAGS],
        operation_summary="Delete Tag",
        operation_description="Delete an existing tag (Admin only)",
        responses={
            204: openapi.Response("Tag deleted successfully"),
            401: openapi.Response("Unauthorized - Admin access required"),
            404: openapi.Response("Tag not found"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a tag."""
        return super().destroy(request, *args, **kwargs)

    def get_permissions(self):
        """Set permissions based on action."""
        return [IsAdminOrReadOnly()]
