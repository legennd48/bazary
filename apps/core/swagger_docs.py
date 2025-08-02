"""
Centralized Swagger documentation configuration and examples.
"""

from drf_yasg import openapi
import os
import json
from pathlib import Path
from django.conf import settings


def get_captured_example(endpoint_name, method, status_code):
    """
    Get a captured example from the filesystem.
    
    Args:
        endpoint_name: Name of the endpoint (e.g., 'auth_register')
        method: HTTP method (e.g., 'POST')
        status_code: HTTP status code (e.g., 201)
        
    Returns:
        dict or None: The captured example response data
    """
    filename = f"{endpoint_name}_{method.lower()}_{status_code}.json"
    filepath = os.path.join(settings.BASE_DIR, 'swagger_examples', filename)
    
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                
                # Extract only the response_data for Swagger UI
                if 'response_data' in data:
                    return data['response_data']
                else:
                    return data
    except Exception as e:
        # Silently handle errors in production
        pass
    
    return None


def get_example_or_fallback(endpoint_name, method, status_code, fallback_example):
    """
    Get captured example or fall back to manual example.
    
    Args:
        endpoint_name: Name of the endpoint
        method: HTTP method
        status_code: HTTP status code
        fallback_example: Manual fallback example
        
    Returns:
        dict: Example data
    """
    captured = get_captured_example(endpoint_name, method, status_code)
    return captured if captured is not None else fallback_example
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status


class SwaggerTags:
    """Standard tags for API documentation."""
    AUTHENTICATION = "Authentication"
    PRODUCTS = "Products"
    CATEGORIES = "Categories"
    TAGS = "Tags"
    USERS = "Users"


class SwaggerResponses:
    """Standard response schemas for common HTTP status codes."""
    
    @staticmethod
    def success(description="Success"):
        return {200: openapi.Response(description)}
    
    @staticmethod
    def created(description="Created"):
        return {201: openapi.Response(description)}
    
    @staticmethod
    def no_content(description="No Content"):
        return {204: openapi.Response(description)}
    
    @staticmethod
    def bad_request(description="Bad Request"):
        return {400: openapi.Response(description)}
    
    @staticmethod
    def unauthorized(description="Unauthorized"):
        return {401: openapi.Response(description)}
    
    @staticmethod
    def forbidden(description="Forbidden"):
        return {403: openapi.Response(description)}
    
    @staticmethod
    def not_found(description="Not Found"):
        return {404: openapi.Response(description)}
    
    @staticmethod
    def validation_error(description="Validation Error"):
        return {400: openapi.Response(
            description,
            examples={
                "application/json": {
                    "field_name": ["This field is required."],
                    "non_field_errors": ["Invalid data provided."]
                }
            }
        )}
    
    @staticmethod
    def standard_crud():
        """Standard CRUD operation responses."""
        return {
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request - Validation errors"),
            401: openapi.Response("Unauthorized - Authentication required"),
            403: openapi.Response("Forbidden - Permission denied"),
            404: openapi.Response("Not Found"),
            500: openapi.Response("Internal Server Error")
        }


class SwaggerExamples:
    """Example data for API documentation."""
    
    # Product Examples
    PRODUCT_CREATE_EXAMPLE = {
        "name": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.",
        "short_description": "Premium wireless headphones with noise cancellation",
        "price": "299.99",
        "category": 1,
        "sku": "WH-XB900N",
        "stock_quantity": 50,
        "track_inventory": True,
        "is_featured": True,
        "is_active": True,
        "tags": [1, 2, 3]
    }
    
    PRODUCT_RESPONSE_EXAMPLE = {
        "id": 1,
        "name": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.",
        "short_description": "Premium wireless headphones with noise cancellation",
        "price": "299.99",
        "category": {
            "id": 1,
            "name": "Electronics",
            "slug": "electronics"
        },
        "sku": "WH-XB900N",
        "stock_quantity": 50,
        "track_inventory": True,
        "is_featured": True,
        "is_active": True,
        "is_in_stock": True,
        "is_low_stock": False,
        "tags": [
            {"id": 1, "name": "wireless"},
            {"id": 2, "name": "headphones"},
            {"id": 3, "name": "premium"}
        ],
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
        "created_by": {
            "id": "user-uuid",
            "email": "admin@bazary.com",
            "username": "admin"
        }
    }
    
    # Authentication Examples
    REGISTER_EXAMPLE = {
        "email": "user@example.com",
        "username": "newuser",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    
    LOGIN_EXAMPLE = {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    
    LOGIN_RESPONSE_EXAMPLE = {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": "user-uuid",
            "email": "user@example.com",
            "username": "newuser",
            "first_name": "John",
            "last_name": "Doe"
        }
    }
    
    # Category Examples
    CATEGORY_CREATE_EXAMPLE = {
        "name": "Electronics",
        "description": "Electronic devices and accessories",
        "parent": None,
        "is_active": True,
        "sort_order": 1
    }
    
    # Tag Examples
    TAG_CREATE_EXAMPLE = {
        "name": "wireless",
        "description": "Wireless technology products"
    }


class SwaggerParameters:
    """Common parameter definitions for API documentation."""
    
    SEARCH_QUERY = openapi.Parameter(
        'q',
        openapi.IN_QUERY,
        description="Search query to filter results by name, description, or other searchable fields",
        type=openapi.TYPE_STRING,
        required=False
    )
    
    PAGE = openapi.Parameter(
        'page',
        openapi.IN_QUERY,
        description="Page number for pagination (default: 1)",
        type=openapi.TYPE_INTEGER,
        required=False
    )
    
    PAGE_SIZE = openapi.Parameter(
        'page_size',
        openapi.IN_QUERY,
        description="Number of results per page (default: 20, max: 100)",
        type=openapi.TYPE_INTEGER,
        required=False
    )
    
    ORDERING = openapi.Parameter(
        'ordering',
        openapi.IN_QUERY,
        description="Field to order results by. Prefix with '-' for descending order",
        type=openapi.TYPE_STRING,
        required=False
    )
    
    # Product-specific parameters
    CATEGORY_FILTER = openapi.Parameter(
        'category',
        openapi.IN_QUERY,
        description="Filter products by category ID",
        type=openapi.TYPE_INTEGER,
        required=False
    )
    
    PRICE_MIN = openapi.Parameter(
        'price_min',
        openapi.IN_QUERY,
        description="Minimum price filter",
        type=openapi.TYPE_NUMBER,
        required=False
    )
    
    PRICE_MAX = openapi.Parameter(
        'price_max',
        openapi.IN_QUERY,
        description="Maximum price filter",
        type=openapi.TYPE_NUMBER,
        required=False
    )
    
    IS_FEATURED = openapi.Parameter(
        'is_featured',
        openapi.IN_QUERY,
        description="Filter by featured products (true/false)",
        type=openapi.TYPE_BOOLEAN,
        required=False
    )
    
    IN_STOCK = openapi.Parameter(
        'in_stock',
        openapi.IN_QUERY,
        description="Filter by stock availability (true/false)",
        type=openapi.TYPE_BOOLEAN,
        required=False
    )


class TestingInstructions:
    """Testing instructions and examples for API endpoints."""
    
    PRODUCTS_TESTING = """
## Product API Testing Instructions

### Prerequisites
1. **Authentication**: Most write operations require admin authentication
2. **Test Data**: Ensure you have categories and tags created first
3. **Base URL**: All endpoints use `/api/v1/products/` prefix

### Testing Scenarios

#### 1. List Products (Public Access)
```bash
curl -X GET "http://localhost:8000/api/v1/products/"
```
**Expected**: 200 OK with paginated product list

#### 2. Search Products
```bash
curl -X GET "http://localhost:8000/api/v1/products/search/?q=headphones&category=1&price_min=100&price_max=500"
```
**Expected**: 200 OK with filtered results

#### 3. Get Featured Products
```bash
curl -X GET "http://localhost:8000/api/v1/products/featured/"
```
**Expected**: 200 OK with featured products only

#### 4. Create Product (Admin Required)
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Test Product",
    "description": "Test Description",
    "price": "99.99",
    "category": 1,
    "sku": "TEST-001"
  }'
```
**Expected**: 201 Created with product data

#### 5. Update Stock (Admin Required)
```bash
curl -X POST "http://localhost:8000/api/v1/products/1/update_stock/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"quantity": 25}'
```
**Expected**: 200 OK with updated stock info

### Error Cases to Test
- **401 Unauthorized**: Try creating/updating without token
- **403 Forbidden**: Try admin operations with regular user token
- **400 Bad Request**: Send invalid data (missing required fields, invalid price)
- **404 Not Found**: Request non-existent product ID

### Performance Testing
- **Large Dataset**: Test with 1000+ products for pagination performance
- **Complex Filters**: Combine multiple filters to test query optimization
- **Concurrent Requests**: Test simultaneous read/write operations
"""

    AUTHENTICATION_TESTING = """
## Authentication API Testing Instructions

### Base URL
All endpoints use `/api/v1/auth/` prefix

### Testing Flow

#### 1. User Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

#### 2. User Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```
**Save the access_token for subsequent requests**

#### 3. Get User Profile
```bash
curl -X GET "http://localhost:8000/api/v1/auth/profile/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. Token Refresh
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token/refresh/" \\
  -H "Content-Type: application/json" \\
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### Security Testing
- **Password Strength**: Test weak passwords (should fail)
- **Email Validation**: Test invalid email formats
- **Token Expiry**: Test with expired tokens
- **Duplicate Registration**: Try registering same email twice
"""


def get_testing_instructions_response(app_name: str) -> openapi.Response:
    """Get testing instructions response for a specific app."""
    instructions_map = {
        'products': TestingInstructions.PRODUCTS_TESTING,
        'authentication': TestingInstructions.AUTHENTICATION_TESTING,
    }
    
    instructions = instructions_map.get(app_name, "Testing instructions not available for this app.")
    
    return openapi.Response(
        description=f"Testing instructions for {app_name.title()} API",
        examples={
            "text/markdown": instructions
        }
    )
