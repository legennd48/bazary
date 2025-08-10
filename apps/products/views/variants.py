"""
Product variant management views.
"""

from django.db import transaction

from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrReadOnly
from apps.core.swagger_docs import SwaggerTags
from apps.products.models import (
    ProductVariant,
    ProductVariantImage,
    VariantOption,
    VariantOptionValue,
)
from apps.products.serializers import (
    ProductVariantCreateUpdateSerializer,
    ProductVariantDetailSerializer,
    ProductVariantListSerializer,
    VariantOptionSerializer,
    VariantOptionValueSerializer,
    VariantOptionWithValuesSerializer,
)


class VariantOptionViewSet(viewsets.ModelViewSet):
    """
    ## Variant Option Management

    Manage variant options like Color, Size, Material, etc.

    ### Features:
    - Create and manage option types (Color, Size, etc.)
    - Set display types (dropdown, color picker, buttons)
    - Configure option requirements
    - Order options for display
    """

    queryset = VariantOption.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["display_type", "is_required"]
    search_fields = ["name", "display_name"]
    ordering_fields = ["sort_order", "name", "created_at"]
    ordering = ["sort_order", "name"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list" or self.action == "retrieve":
            return VariantOptionWithValuesSerializer
        return VariantOptionSerializer

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="List Variant Options",
        operation_description="Get paginated list of variant options with their values",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Variant Option Details",
        operation_description="Get detailed information about a variant option including all its values",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Create Variant Option",
        operation_description="Create a new variant option (e.g., Color, Size)",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Update Variant Option",
        operation_description="Update an existing variant option",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.VARIANT_OPTIONS],
        operation_summary="Partial Update Variant Option",
        operation_description="Partially update an existing variant option",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Delete Variant Option",
        operation_description="Delete a variant option (will also delete all its values)",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class VariantOptionValueViewSet(viewsets.ModelViewSet):
    """
    ## Variant Option Value Management

    Manage values for variant options (e.g., Red, Blue for Color; S, M, L for Size).

    ### Features:
    - Create values for specific options
    - Set display names and colors
    - Upload value images
    - Order values for display
    """

    queryset = VariantOptionValue.objects.all()
    serializer_class = VariantOptionValueSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["option", "option__name"]
    search_fields = ["value", "display_name"]
    ordering_fields = ["sort_order", "value", "created_at"]
    ordering = ["sort_order", "value"]

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="List Variant Option Values",
        operation_description="Get paginated list of variant option values",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Option Value Details",
        operation_description="Get detailed information about a variant option value",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Create Option Value",
        operation_description="Create a new value for a variant option",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Update Option Value",
        operation_description="Update an existing variant option value",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.VARIANT_OPTIONS],
        operation_summary="Partial Update Option Value",
        operation_description="Partially update an existing variant option value",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Delete Option Value",
        operation_description="Delete a variant option value",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    ## Product Variant Management

    Manage individual product variants with their specific pricing, inventory, and attributes.

    ### Features:
    - Create variants for products
    - Set variant-specific pricing and inventory
    - Manage variant options (size, color, etc.)
    - Upload variant-specific images
    - Track variant stock and sales
    """

    queryset = ProductVariant.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "product",
        "is_active",
        "option_values__option",
        "option_values__value",
    ]
    search_fields = ["sku", "product__name"]
    ordering_fields = ["sku", "price", "stock_quantity", "created_at"]
    ordering = ["sku"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ProductVariantListSerializer
        elif self.action == "retrieve":
            return ProductVariantDetailSerializer
        return ProductVariantCreateUpdateSerializer

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="List Product Variants",
        operation_description="Get paginated list of product variants",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Variant Details",
        operation_description="Get detailed information about a product variant",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Create Product Variant",
        operation_description="Create a new variant for a product with option values",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Update Product Variant",
        operation_description="Update an existing product variant",
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCT_VARIANTS],
        operation_summary="Partial Update Product Variant",
        operation_description="Partially update an existing product variant",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Delete Product Variant",
        operation_description="Delete a product variant",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Upload Variant Images",
        operation_description="Upload images specific to this variant",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "images": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE),
                    description="Array of image files",
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Images uploaded successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Images uploaded successfully",
                        "uploaded_count": 3,
                    }
                },
            )
        },
    )
    @action(detail=True, methods=["post"], url_path="upload-images")
    def upload_images(self, request, pk=None):
        """Upload images for a specific variant."""
        variant = self.get_object()
        images = request.FILES.getlist("images")

        if not images:
            return Response(
                {"success": False, "message": "No images provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded_count = 0
        try:
            with transaction.atomic():
                for index, image in enumerate(images):
                    ProductVariantImage.objects.create(
                        variant=variant,
                        image=image,
                        sort_order=index,
                        is_primary=(
                            index == 0
                            and not variant.images.filter(is_primary=True).exists()
                        ),
                    )
                    uploaded_count += 1

            return Response(
                {
                    "success": True,
                    "message": "Images uploaded successfully",
                    "uploaded_count": uploaded_count,
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "message": f"Image upload failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Get Available Options",
        operation_description="Get available variant options for creating new variants",
        responses={
            200: openapi.Response(
                description="Available variant options",
                examples={
                    "application/json": {
                        "options": [
                            {
                                "id": 1,
                                "name": "color",
                                "display_name": "Color",
                                "display_type": "color",
                                "values": [
                                    {
                                        "id": 1,
                                        "value": "red",
                                        "display_name": "Red",
                                        "color_code": "#ff0000",
                                    },
                                    {
                                        "id": 2,
                                        "value": "blue",
                                        "display_name": "Blue",
                                        "color_code": "#0000ff",
                                    },
                                ],
                            }
                        ]
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="available-options")
    def available_options(self, request):
        """Get all available variant options for creating variants."""
        options = VariantOption.objects.prefetch_related("values").all()
        serializer = VariantOptionWithValuesSerializer(options, many=True)

        return Response({"options": serializer.data})

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Bulk Update Stock",
        operation_description="Update stock quantities for multiple variants",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "variants": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                            "stock_quantity": openapi.Schema(type=openapi.TYPE_INTEGER),
                        },
                    ),
                )
            },
        ),
        responses={
            200: openapi.Response(
                description="Stock updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Stock updated for 5 variants",
                        "updated_count": 5,
                    }
                },
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="bulk-update-stock")
    def bulk_update_stock(self, request):
        """Update stock quantities for multiple variants."""
        variants_data = request.data.get("variants", [])

        if not variants_data:
            return Response(
                {"success": False, "message": "No variant data provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_count = 0
        try:
            with transaction.atomic():
                for variant_data in variants_data:
                    variant_id = variant_data.get("id")
                    stock_quantity = variant_data.get("stock_quantity")

                    if variant_id is None or stock_quantity is None:
                        continue

                    try:
                        variant = ProductVariant.objects.get(id=variant_id)
                        variant.stock_quantity = stock_quantity
                        variant.save()
                        updated_count += 1
                    except ProductVariant.DoesNotExist:
                        continue

            return Response(
                {
                    "success": True,
                    "message": f"Stock updated for {updated_count} variants",
                    "updated_count": updated_count,
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "message": f"Bulk stock update failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
