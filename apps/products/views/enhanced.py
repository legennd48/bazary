"""
Enhanced product views for advanced product management.
"""

import csv
import io
from decimal import Decimal

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsAdminOrReadOnly
from apps.core.swagger_docs import SwaggerTags
from apps.products.models import Product, ProductImage, Tag
from apps.products.serializers import (
    ProductBulkOperationSerializer,
    ProductExportSerializer,
)


class ProductManagementViewSet(viewsets.GenericViewSet):
    """
    Advanced product management operations.
    
    Provides bulk operations, import/export, and media management.
    """
    
    permission_classes = [IsAdminOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductBulkOperationSerializer  # Default serializer for Swagger

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Bulk Product Operations",
        operation_description="Perform bulk operations on multiple products",
        request_body=ProductBulkOperationSerializer,
        responses={
            200: openapi.Response(
                description="Bulk operation completed",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Bulk operation completed successfully",
                        "affected_count": 5,
                        "operation": "activate"
                    }
                }
            )
        }
    )
    @action(detail=False, methods=["post"])
    def bulk_operations(self, request):
        """Perform bulk operations on products."""
        serializer = ProductBulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        action_type = data["action"]
        product_ids = data["product_ids"]
        
        # Get products
        products = Product.objects.filter(id__in=product_ids)
        affected_count = 0

        try:
            with transaction.atomic():
                if action_type == "activate":
                    affected_count = products.update(is_active=True)
                
                elif action_type == "deactivate":
                    affected_count = products.update(is_active=False)
                
                elif action_type == "update_price":
                    price_adjustment = data["price_adjustment"]
                    adjustment_type = data.get("price_adjustment_type", "set")
                    
                    for product in products:
                        if adjustment_type == "set":
                            product.price = price_adjustment
                        elif adjustment_type == "increase":
                            product.price += price_adjustment
                        elif adjustment_type == "decrease":
                            product.price = max(Decimal("0.01"), product.price - price_adjustment)
                        product.save()
                        affected_count += 1
                
                elif action_type == "update_stock":
                    stock_quantity = data["stock_quantity"]
                    affected_count = products.update(stock_quantity=stock_quantity)
                
                elif action_type == "assign_category":
                    category_id = data["category_id"]
                    affected_count = products.update(category_id=category_id)
                
                elif action_type == "add_tags":
                    tag_ids = data["tag_ids"]
                    for product in products:
                        product.tags.add(*tag_ids)
                        affected_count += 1
                
                elif action_type == "remove_tags":
                    tag_ids = data["tag_ids"]
                    for product in products:
                        product.tags.remove(*tag_ids)
                        affected_count += 1
                
                elif action_type == "delete":
                    affected_count = products.count()
                    products.delete()

            return Response({
                "success": True,
                "message": f"Bulk {action_type} operation completed successfully",
                "affected_count": affected_count,
                "operation": action_type
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Bulk operation failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Upload Product Images",
        operation_description="Upload multiple images for a product",
        manual_parameters=[
            openapi.Parameter(
                "product_id",
                openapi.IN_PATH,
                description="Product ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                "images",
                openapi.IN_FORM,
                description="Image files to upload",
                type=openapi.TYPE_FILE,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Images uploaded successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Images uploaded successfully",
                        "uploaded_count": 3
                    }
                }
            )
        }
    )
    @action(
        detail=True, 
        methods=["post"], 
        parser_classes=[MultiPartParser, FileUploadParser],
        url_path="upload-images"
    )
    def upload_images(self, request, pk=None):
        """Upload multiple images for a product."""
        try:
            product = self.get_object()
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Handle multiple image files
        images = request.FILES.getlist("images")
        if not images:
            return Response({
                "success": False,
                "message": "No images provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        uploaded_count = 0
        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                sort_order=index,
                is_primary=(index == 0 and not product.images.filter(is_primary=True).exists())
            )
            uploaded_count += 1

        return Response({
            "success": True,
            "message": "Images uploaded successfully",
            "uploaded_count": uploaded_count
        })

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Import Products",
        operation_description="Import products from CSV or Excel file",
        manual_parameters=[
            openapi.Parameter(
                "file",
                openapi.IN_FORM,
                description="CSV or Excel file containing product data",
                type=openapi.TYPE_FILE,
                required=True
            ),
            openapi.Parameter(
                "update_existing",
                openapi.IN_FORM,
                description="Whether to update existing products with the same SKU",
                type=openapi.TYPE_BOOLEAN,
                default=False
            ),
            openapi.Parameter(
                "validate_only",
                openapi.IN_FORM,
                description="Only validate the data without importing",
                type=openapi.TYPE_BOOLEAN,
                default=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Products imported successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Products imported successfully",
                        "imported_count": 25,
                        "updated_count": 5,
                        "errors": []
                    }
                }
            )
        }
    )
    @action(
        detail=False, 
        methods=["post"], 
        parser_classes=[MultiPartParser, FileUploadParser]
    )
    def import_products(self, request):
        """Import products from CSV or Excel file."""
        # Handle file upload directly
        file = request.FILES.get("file")
        if not file:
            return Response({
                "success": False,
                "message": "No file provided"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get parameters
        update_existing = request.data.get("update_existing", "false").lower() == "true"
        validate_only = request.data.get("validate_only", "false").lower() == "true"

        # Validate file format
        allowed_extensions = [".csv", ".xlsx", ".xls"]
        file_extension = "." + file.name.split(".")[-1].lower()
        
        if file_extension not in allowed_extensions:
            return Response({
                "success": False,
                "message": f"File must be one of: {', '.join(allowed_extensions)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            return Response({
                "success": False,
                "message": "File size cannot exceed 10MB"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read file content
            if file.name.endswith('.csv'):
                content = file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(content))
            else:
                # For Excel files, you would need openpyxl or pandas
                return Response({
                    "success": False,
                    "message": "Excel import not implemented yet"
                }, status=status.HTTP_400_BAD_REQUEST)

            imported_count = 0
            updated_count = 0
            errors = []

            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Basic validation and processing
                        name = row.get("name", "").strip()
                        if not name:
                            errors.append(f"Row {row_num}: Name is required")
                            continue

                        sku = row.get("sku", "").strip()
                        if not sku:
                            errors.append(f"Row {row_num}: SKU is required")
                            continue

                        # Check if product exists
                        existing_product = Product.objects.filter(sku=sku).first()
                        
                        if existing_product and not update_existing:
                            errors.append(f"Row {row_num}: Product with SKU {sku} already exists")
                            continue

                        product_data = {
                            "name": name,
                            "sku": sku,
                            "description": row.get("description", ""),
                            "short_description": row.get("short_description", ""),
                            "price": Decimal(row.get("price", "0")),
                        }

                        if validate_only:
                            # Just validate, don't save
                            continue

                        if existing_product:
                            # Update existing product
                            for key, value in product_data.items():
                                setattr(existing_product, key, value)
                            existing_product.save()
                            updated_count += 1
                        else:
                            # Create new product
                            Product.objects.create(**product_data)
                            imported_count += 1

                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")

                if validate_only:
                    return Response({
                        "success": True,
                        "message": "Validation completed",
                        "validation_errors": errors
                    })

            return Response({
                "success": True,
                "message": "Products imported successfully",
                "imported_count": imported_count,
                "updated_count": updated_count,
                "errors": errors
            })

        except Exception as e:
            return Response({
                "success": False,
                "message": f"Import failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=[SwaggerTags.PRODUCTS],
        operation_summary="Export Products",
        operation_description="Export products to CSV or Excel format",
        query_serializer=ProductExportSerializer,
        responses={
            200: openapi.Response(
                description="Products exported successfully (file download)",
                content_type="text/csv"
            )
        }
    )
    @action(detail=False, methods=["get"])
    def export_products(self, request):
        """Export products to CSV or Excel format."""
        serializer = ProductExportSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        format_type = data.get("format", "csv")
        include_variants = data.get("include_variants", True)
        include_images = data.get("include_images", False)

        # Build queryset with filters
        queryset = Product.objects.all()
        
        if "category_ids" in data:
            queryset = queryset.filter(category_id__in=data["category_ids"])
        
        if "tag_ids" in data:
            queryset = queryset.filter(tags__id__in=data["tag_ids"])
        
        if "is_active" in data:
            queryset = queryset.filter(is_active=data["is_active"])
        
        if "date_from" in data:
            queryset = queryset.filter(created_at__gte=data["date_from"])
        
        if "date_to" in data:
            queryset = queryset.filter(created_at__lte=data["date_to"])

        # Create CSV response
        response = HttpResponse(content_type="text/csv")
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response["Content-Disposition"] = f'attachment; filename="products_export_{timestamp}.csv"'

        writer = csv.writer(response)
        
        # Write header
        header = [
            "id", "name", "slug", "description", "short_description", "sku",
            "price", "compare_price", "category", "tags", "stock_quantity",
            "is_active", "is_featured", "is_digital", "created_at"
        ]
        
        if include_images:
            header.append("primary_image_url")
        
        if include_variants:
            header.extend(["variants_count", "variant_skus"])
        
        writer.writerow(header)

        # Write data
        for product in queryset:
            row = [
                product.id,
                product.name,
                product.slug,
                product.description,
                product.short_description,
                product.sku,
                product.price,
                product.compare_price or "",
                product.category.name if product.category else "",
                ", ".join(tag.name for tag in product.tags.all()),
                product.stock_quantity,
                product.is_active,
                product.is_featured,
                product.is_digital,
                product.created_at.isoformat(),
            ]
            
            if include_images:
                primary_image = product.primary_image
                row.append(primary_image.image.url if primary_image else "")
            
            if include_variants:
                variants = product.variants.all()
                row.extend([
                    variants.count(),
                    ", ".join(variant.sku for variant in variants)
                ])
            
            writer.writerow(row)

        return response
