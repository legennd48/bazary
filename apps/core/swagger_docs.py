"""
Centralized Swagger documentation configuration and examples.
"""

import json
import os
from pathlib import Path

from django.conf import settings

from drf_yasg import openapi


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
    filepath = os.path.join(settings.BASE_DIR, "swagger_examples", filename)

    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)

                # Extract only the response_data for Swagger UI
                if "response_data" in data:
                    return data["response_data"]
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
    """
    🎯 Organized API Tags for Optimal Developer Experience
    
    Tags are strategically ordered to follow the typical user/developer journey:
    1. Start with authentication (essential for most operations)
    2. User management and profiles
    3. Admin operations (grouped by domain)
    4. Product catalog and discovery
    5. Shopping and cart management
    6. Payment processing
    7. System utilities and testing
    
    Each tag includes emojis for visual recognition and priority numbers for sorting.
    """
    
    # 🔐 AUTHENTICATION & ACCOUNT MANAGEMENT (Priority 1)
    AUTHENTICATION = "01 🔐 Authentication"
    EMAIL_VERIFICATION = "02 � Email Verification"  
    PASSWORD_MANAGEMENT = "03 🔑 Password Management"
    TOKEN_MANAGEMENT = "04 🎫 Token Management"
    
    # 👤 USER MANAGEMENT (Priority 2)
    USER_PROFILE = "05 👤 User Profile"
    USER_ADDRESSES = "06 🏠 User Addresses"
    USER_ACTIVITY = "07 � User Activity"
    
    # 🛡️ ADMIN OPERATIONS (Priority 3)
    ADMIN_USER_MANAGEMENT = "08 🛡️ Admin - User Management"
    ADMIN_PRODUCT_MANAGEMENT = "09 🛡️ Admin - Product Management"
    ADMIN_ANALYTICS = "10 🛡️ Admin - Analytics"
    
    # 📂 CATALOG MANAGEMENT (Priority 4)
    CATEGORIES = "11 📂 Categories"
    TAGS = "12 🏷️ Tags"
    
    # 📦 PRODUCT MANAGEMENT (Priority 5)
    PRODUCTS = "13 📦 Products"
    PRODUCT_VARIANTS = "14 � Product Variants"
    PRODUCT_IMAGES = "15 �️ Product Images"
    VARIANT_OPTIONS = "16 ⚙️ Variant Options"
    
    # 🛒 SHOPPING EXPERIENCE (Priority 6)
    PRODUCT_DISCOVERY = "17 � Product Discovery"
    PRODUCT_SEARCH = "18 🔎 Search & Filters"
    SHOPPING_CART = "19 🛒 Shopping Cart"
    CART_MANAGEMENT = "20 �️ Cart Management"
    
    # 💳 PAYMENT & CHECKOUT (Priority 7)
    PAYMENT_PROVIDERS = "21 🏦 Payment Providers"
    PAYMENT_METHODS = "22 💳 Payment Methods"
    TRANSACTIONS = "23 � Transactions"
    PAYMENT_WEBHOOKS = "24 � Payment Webhooks"
    PAYMENT_CALLBACKS = "25 � Payment Callbacks"
    
    # 🔧 SYSTEM & UTILITIES (Priority 8)
    SYSTEM_HEALTH = "26 🏥 System Health"
    API_TESTING = "27 🧪 API Testing"
    UTILITIES = "28 🔧 Utilities"
    
    # 📚 DOCUMENTATION & GUIDES (Priority 9)
    TESTING_GUIDES = "29 📚 Testing Guides"
    API_DOCUMENTATION = "30 📖 API Documentation"
    
    # ⚠️ Legacy tags (for backward compatibility - marked for migration)
    USERS = USER_PROFILE  # Redirect to new tag
    PAYMENT = PAYMENT_PROVIDERS  # Redirect to new tag


# Enhanced Tag Descriptions for better documentation
TAG_DESCRIPTIONS = {
    SwaggerTags.AUTHENTICATION: {
        "description": "Core authentication endpoints for user login, registration, and session management. Start here for API access.",
        "external_docs": {
            "description": "Authentication Guide",
            "url": "https://docs.bazary.com/auth"
        }
    },
    SwaggerTags.EMAIL_VERIFICATION: {
        "description": "Email verification and account activation endpoints. Required for new user accounts.",
    },
    SwaggerTags.PASSWORD_MANAGEMENT: {
        "description": "Password reset and recovery endpoints for account security management.",
    },
    SwaggerTags.TOKEN_MANAGEMENT: {
        "description": "JWT token operations including refresh, verify, and blacklist functionality.",
    },
    SwaggerTags.USER_PROFILE: {
        "description": "User profile management, settings, and personal information endpoints.",
    },
    SwaggerTags.USER_ADDRESSES: {
        "description": "User shipping and billing address management for checkout and delivery.",
    },
    SwaggerTags.USER_ACTIVITY: {
        "description": "User activity tracking, audit logs, and behavioral analytics.",
    },
    SwaggerTags.ADMIN_USER_MANAGEMENT: {
        "description": "Administrative user management operations. Requires admin privileges.",
    },
    SwaggerTags.ADMIN_PRODUCT_MANAGEMENT: {
        "description": "Administrative product management and bulk operations. Requires admin privileges.",
    },
    SwaggerTags.CATEGORIES: {
        "description": "Product category management with hierarchical organization support.",
    },
    SwaggerTags.TAGS: {
        "description": "Product tagging system for flexible organization and filtering.",
    },
    SwaggerTags.PRODUCTS: {
        "description": "Core product management with CRUD operations, search, and filtering capabilities.",
        "external_docs": {
            "description": "Product API Guide", 
            "url": "https://docs.bazary.com/products"
        }
    },
    SwaggerTags.PRODUCT_VARIANTS: {
        "description": "Product variant management for size, color, and other product options.",
    },
    SwaggerTags.VARIANT_OPTIONS: {
        "description": "Variant option definitions and value management for product customization.",
    },
    SwaggerTags.PRODUCT_DISCOVERY: {
        "description": "Product browsing, featured products, and discovery endpoints for customers.",
    },
    SwaggerTags.PRODUCT_SEARCH: {
        "description": "Advanced product search with filters, sorting, and faceted search capabilities.",
    },
    SwaggerTags.SHOPPING_CART: {
        "description": "Shopping cart operations for managing customer product selections.",
    },
    SwaggerTags.CART_MANAGEMENT: {
        "description": "Advanced cart management including bulk operations and cart persistence.",
    },
    SwaggerTags.PAYMENT_PROVIDERS: {
        "description": "Payment provider configuration and management (Chapa, Stripe, etc.).",
    },
    SwaggerTags.PAYMENT_METHODS: {
        "description": "Payment method management for customers and transaction processing.",
    },
    SwaggerTags.TRANSACTIONS: {
        "description": "Transaction processing, tracking, and payment flow management.",
    },
    SwaggerTags.PAYMENT_WEBHOOKS: {
        "description": "Webhook endpoints for payment provider notifications and status updates.",
    },
    SwaggerTags.SYSTEM_HEALTH: {
        "description": "System health checks, monitoring, and status endpoints.",
    },
    SwaggerTags.API_TESTING: {
        "description": "API testing utilities and development helper endpoints.",
    },
    SwaggerTags.TESTING_GUIDES: {
        "description": "Comprehensive testing instructions and examples for each API module.",
    },
}


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
        return {
            400: openapi.Response(
                description,
                examples={
                    "application/json": {
                        "field_name": ["This field is required."],
                        "non_field_errors": ["Invalid data provided."],
                    }
                },
            )
        }

    @staticmethod
    def standard_crud():
        """Standard CRUD operation responses."""
        return {
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request - Validation errors"),
            401: openapi.Response("Unauthorized - Authentication required"),
            403: openapi.Response("Forbidden - Permission denied"),
            404: openapi.Response("Not Found"),
            500: openapi.Response("Internal Server Error"),
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
        "tags": [1, 2, 3],
    }

    PRODUCT_RESPONSE_EXAMPLE = {
        "id": 1,
        "name": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.",
        "short_description": "Premium wireless headphones with noise cancellation",
        "price": "299.99",
        "category": {"id": 1, "name": "Electronics", "slug": "electronics"},
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
            {"id": 3, "name": "premium"},
        ],
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
        "created_by": {
            "id": "user-uuid",
            "email": "admin@bazary.com",
            "username": "admin",
        },
    }

    # Authentication Examples
    REGISTER_EXAMPLE = {
        "email": "user@example.com",
        "username": "newuser",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
    }

    LOGIN_EXAMPLE = {"email": "user@example.com", "password": "SecurePass123!"}

    LOGIN_RESPONSE_EXAMPLE = {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": "user-uuid",
            "email": "user@example.com",
            "username": "newuser",
            "first_name": "John",
            "last_name": "Doe",
        },
    }

    # Category Examples
    CATEGORY_CREATE_EXAMPLE = {
        "name": "Electronics",
        "description": "Electronic devices and accessories",
        "parent": None,
        "is_active": True,
        "sort_order": 1,
    }

    CATEGORY_RESPONSE_EXAMPLE = {
        "id": 1,
        "name": "Electronics",
        "description": "Electronic devices and accessories",
        "slug": "electronics",
        "parent": None,
        "is_active": True,
        "sort_order": 1,
        "image": None,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z",
        "subcategories": [
            {"id": 2, "name": "Smartphones", "slug": "smartphones"},
            {"id": 3, "name": "Laptops", "slug": "laptops"},
        ],
        "product_count": 45,
    }

    # Tag Examples
    TAG_CREATE_EXAMPLE = {
        "name": "wireless",
        "description": "Wireless technology products",
    }


class SwaggerParameters:
    """Common parameter definitions for API documentation."""

    SEARCH_QUERY = openapi.Parameter(
        "q",
        openapi.IN_QUERY,
        description="Search query to filter results by name, description, or other searchable fields",
        type=openapi.TYPE_STRING,
        required=False,
    )

    PAGE = openapi.Parameter(
        "page",
        openapi.IN_QUERY,
        description="Page number for pagination (default: 1)",
        type=openapi.TYPE_INTEGER,
        required=False,
    )

    PAGE_SIZE = openapi.Parameter(
        "page_size",
        openapi.IN_QUERY,
        description="Number of results per page (default: 20, max: 100)",
        type=openapi.TYPE_INTEGER,
        required=False,
    )

    ORDERING = openapi.Parameter(
        "ordering",
        openapi.IN_QUERY,
        description="Field to order results by. Prefix with '-' for descending order",
        type=openapi.TYPE_STRING,
        required=False,
    )

    # Product-specific parameters
    CATEGORY_FILTER = openapi.Parameter(
        "category",
        openapi.IN_QUERY,
        description="Filter products by category ID",
        type=openapi.TYPE_INTEGER,
        required=False,
    )

    PRICE_MIN = openapi.Parameter(
        "price_min",
        openapi.IN_QUERY,
        description="Minimum price filter",
        type=openapi.TYPE_NUMBER,
        required=False,
    )

    PRICE_MAX = openapi.Parameter(
        "price_max",
        openapi.IN_QUERY,
        description="Maximum price filter",
        type=openapi.TYPE_NUMBER,
        required=False,
    )

    IS_FEATURED = openapi.Parameter(
        "is_featured",
        openapi.IN_QUERY,
        description="Filter by featured products (true/false)",
        type=openapi.TYPE_BOOLEAN,
        required=False,
    )

    IN_STOCK = openapi.Parameter(
        "in_stock",
        openapi.IN_QUERY,
        description="Filter by stock availability (true/false)",
        type=openapi.TYPE_BOOLEAN,
        required=False,
    )


class TestingInstructions:
    """Comprehensive testing instructions and examples for all API endpoints."""

    AUTHENTICATION_TESTING = """
# 🔐 Authentication API Testing Guide

## Base URL: `/api/v1/auth/`

### 📋 Complete Authentication Flow

#### 1. User Registration
```bash
curl -X POST "http://localhost:8001/api/v1/auth/register/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
  }'
```
**Expected**: 201 Created with user data + verification email sent

#### 2. Email Verification
```bash
# Via API (POST)
curl -X POST "http://localhost:8001/api/v1/auth/verify-email/" \\
  -H "Content-Type: application/json" \\
  -d '{"token": "YOUR_VERIFICATION_TOKEN"}'

# Via Link (GET) - click email link or:
curl "http://localhost:8001/api/v1/auth/verify-email/?token=YOUR_TOKEN"
```

#### 3. User Login
```bash
curl -X POST "http://localhost:8001/api/v1/auth/token/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```
**Save the access & refresh tokens!**

#### 4. Access Protected Resources
```bash
curl -X GET "http://localhost:8001/api/v1/auth/profile/" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 5. Token Refresh
```bash
curl -X POST "http://localhost:8001/api/v1/auth/token/refresh/" \\
  -H "Content-Type: application/json" \\
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### 🔄 Password Reset Flow
```bash
# 1. Request reset
curl -X POST "http://localhost:8001/api/v1/auth/password-reset/" \\
  -d '{"email": "test@example.com"}'

# 2. Confirm reset with token from email
curl -X POST "http://localhost:8001/api/v1/auth/password-reset/confirm/" \\
  -d '{
    "token": "RESET_TOKEN", 
    "new_password": "NewSecurePass123!"
  }'
```

### 🧪 Error Testing Scenarios
- **400 Bad Request**: Invalid email format, weak password
- **401 Unauthorized**: Wrong credentials, expired token
- **409 Conflict**: Email already exists
- **429 Too Many Requests**: Rate limiting triggered
"""

    PRODUCTS_TESTING = """
# 📦 Products API Testing Guide

## Base URL: `/api/v1/products/`

### 🛒 Customer Flow (Public Access)

#### 1. Browse All Products
```bash
curl "http://localhost:8001/api/v1/products/products/"
```

#### 2. Search Products
```bash
curl "http://localhost:8001/api/v1/products/products/search/?q=headphones&category=1&price_min=100&price_max=500&ordering=-created_at"
```

#### 3. Get Featured Products
```bash
curl "http://localhost:8001/api/v1/products/products/featured/"
```

#### 4. Product Details
```bash
curl "http://localhost:8001/api/v1/products/products/1/"
```

#### 5. Get Products by Category
```bash
curl "http://localhost:8001/api/v1/products/products/?category=1&in_stock=true"
```

### 🛡️ Admin Operations (Requires Authentication)

#### 1. Create Product
```bash
curl -X POST "http://localhost:8001/api/v1/products/products/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Premium Wireless Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "short_description": "Premium wireless headphones",
    "price": "299.99",
    "compare_price": "399.99",
    "category": 1,
    "tag_ids": [1, 2, 3],
    "sku": "WH-001",
    "stock_quantity": 50,
    "track_inventory": true,
    "is_featured": true,
    "is_active": true
  }'
```

#### 2. Update Stock
```bash
curl -X POST "http://localhost:8001/api/v1/products/products/1/update_stock/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{"quantity": 25}'
```

#### 3. Bulk Operations
```bash
curl -X POST "http://localhost:8001/api/v1/products/management/bulk_activate/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{"product_ids": [1, 2, 3]}'
```

### 🏷️ Product Variants Testing
```bash
# Create variant option (e.g., "Size")
curl -X POST "http://localhost:8001/api/v1/products/variant-options/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{"name": "Size", "display_type": "radio"}'

# Create variant option value (e.g., "Large")
curl -X POST "http://localhost:8001/api/v1/products/variant-option-values/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{"option": 1, "value": "Large", "sort_order": 2}'

# Create product variant
curl -X POST "http://localhost:8001/api/v1/products/variants/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{
    "product": 1,
    "option_values": [1, 2],
    "price": "319.99",
    "stock_quantity": 10,
    "sku": "WH-001-L-BLK"
  }'
```
"""

    CATEGORIES_TESTING = """
# 📂 Categories API Testing Guide

## Base URL: `/api/v1/categories/`

### 📱 Basic Operations

#### 1. List All Categories
```bash
curl "http://localhost:8001/api/v1/categories/"
```

#### 2. Get Category Details
```bash
curl "http://localhost:8001/api/v1/categories/1/"
```

#### 3. Create Category (Admin Required)
```bash
curl -X POST "http://localhost:8001/api/v1/categories/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Electronics",
    "description": "Electronic devices and accessories",
    "parent": null,
    "is_active": true,
    "sort_order": 1
  }'
```

#### 4. Create Subcategory
```bash
curl -X POST "http://localhost:8001/api/v1/categories/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{
    "name": "Smartphones",
    "description": "Mobile phones and accessories",
    "parent": 1,
    "is_active": true,
    "sort_order": 1
  }'
```

### 🌳 Hierarchical Testing
- Test deep nesting (categories → subcategories → sub-subcategories)
- Verify product counts are accurate
- Test category filtering in product searches
"""

    PAYMENTS_TESTING = """
# 💳 Payments API Testing Guide

## Base URL: `/api/v1/payments/`

### 🛒 Shopping Cart Flow

#### 1. Create Cart
```bash
curl -X POST "http://localhost:8001/api/v1/payments/carts/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "session-123",
    "currency": "ETB"
  }'
```

#### 2. Add Items to Cart
```bash
curl -X POST "http://localhost:8001/api/v1/payments/carts/1/items/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "product": 1,
    "product_variant": null,
    "quantity": 2,
    "unit_price": "299.99"
  }'
```

#### 3. Update Cart Item
```bash
curl -X PATCH "http://localhost:8001/api/v1/payments/carts/1/items/1/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{"quantity": 3}'
```

#### 4. Get Cart Summary
```bash
curl "http://localhost:8001/api/v1/payments/carts/1/" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 💰 Payment Processing

#### 1. List Payment Providers
```bash
curl "http://localhost:8001/api/v1/payments/providers/"
```

#### 2. Create Payment Method
```bash
curl -X POST "http://localhost:8001/api/v1/payments/methods/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "provider": 1,
    "method_type": "mobile_money",
    "is_default": true
  }'
```

#### 3. Initiate Transaction
```bash
curl -X POST "http://localhost:8001/api/v1/payments/transactions/" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{
    "cart": 1,
    "payment_method": 1,
    "amount": "599.98",
    "currency": "ETB"
  }'
```

### 🔔 Webhook Testing
```bash
# Test Chapa webhook (simulate from Chapa)
curl -X POST "http://localhost:8001/api/v1/payments/webhooks/chapa/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "status": "success",
    "tx_ref": "tx-12345",
    "transaction_id": "chapa-tx-67890",
    "amount": 599.98,
    "currency": "ETB"
  }'
```

### 🧪 Error Scenarios
- **Insufficient Stock**: Try adding more items than available
- **Invalid Payment**: Test with invalid payment methods
- **Cart Conflicts**: Test concurrent cart modifications
"""

    ADMIN_TESTING = """
# 🛡️ Admin Operations Testing Guide

## Prerequisites: Admin Authentication Required

### 👥 User Management

#### 1. List All Users
```bash
curl "http://localhost:8001/api/v1/auth/admin/users/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 2. User Details & Activity
```bash
curl "http://localhost:8001/api/v1/auth/admin/users/USER_ID/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

#### 3. Bulk User Operations
```bash
# Bulk activate users
curl -X POST "http://localhost:8001/api/v1/auth/admin/users/bulk_action/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{
    "action": "activate",
    "user_ids": [1, 2, 3],
    "reason": "Account verification completed"
  }'

# Bulk deactivate users
curl -X POST "http://localhost:8001/api/v1/auth/admin/users/bulk_action/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{
    "action": "deactivate", 
    "user_ids": [4, 5],
    "reason": "Suspicious activity detected"
  }'
```

### 📦 Product Management

#### 1. Advanced Product Operations
```bash
# Bulk product activation
curl -X POST "http://localhost:8001/api/v1/products/management/bulk_activate/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{"product_ids": [1, 2, 3, 4, 5]}'

# Bulk stock update
curl -X POST "http://localhost:8001/api/v1/products/management/bulk_stock_update/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \\
  -d '{
    "updates": [
      {"product_id": 1, "quantity": 100},
      {"product_id": 2, "quantity": 50}
    ]
  }'
```

### 📊 Analytics & Reporting
```bash
# User activity analytics
curl "http://localhost:8001/api/v1/auth/admin/users/USER_ID/activity/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Product performance metrics
curl "http://localhost:8001/api/v1/products/management/analytics/" \\
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```
"""

    COMPLETE_FLOW_TESTING = """
# 🔄 Complete E-Commerce Flow Testing

## 🛍️ End-to-End Customer Journey

### Phase 1: Customer Registration & Setup
```bash
# 1. Register new customer
curl -X POST "http://localhost:8001/api/v1/auth/register/" \\
  -d '{
    "email": "customer@example.com",
    "username": "customer1",
    "password": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Doe"
  }'

# 2. Verify email (use token from email)
curl -X POST "http://localhost:8001/api/v1/auth/verify-email/" \\
  -d '{"token": "VERIFICATION_TOKEN"}'

# 3. Login and get tokens
curl -X POST "http://localhost:8001/api/v1/auth/token/" \\
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!"
  }'
```

### Phase 2: Product Discovery
```bash
# 4. Browse categories
curl "http://localhost:8001/api/v1/categories/"

# 5. Search products
curl "http://localhost:8001/api/v1/products/products/search/?q=wireless&category=1"

# 6. View product details
curl "http://localhost:8001/api/v1/products/products/1/"

# 7. Get featured products
curl "http://localhost:8001/api/v1/products/products/featured/"
```

### Phase 3: Shopping Cart
```bash
# 8. Create cart
curl -X POST "http://localhost:8001/api/v1/payments/carts/" \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{"currency": "ETB"}'

# 9. Add products to cart
curl -X POST "http://localhost:8001/api/v1/payments/carts/1/items/" \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{
    "product": 1,
    "quantity": 2,
    "unit_price": "299.99"
  }'

# 10. Update cart item
curl -X PATCH "http://localhost:8001/api/v1/payments/carts/1/items/1/" \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{"quantity": 1}'
```

### Phase 4: Checkout & Payment
```bash
# 11. Setup payment method
curl -X POST "http://localhost:8001/api/v1/payments/methods/" \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{
    "provider": 1,
    "method_type": "mobile_money",
    "is_default": true
  }'

# 12. Initiate transaction
curl -X POST "http://localhost:8001/api/v1/payments/transactions/" \\
  -H "Authorization: Bearer TOKEN" \\
  -d '{
    "cart": 1,
    "payment_method": 1,
    "amount": "299.99",
    "currency": "ETB"
  }'

# 13. Verify payment status
curl "http://localhost:8001/api/v1/payments/transactions/1/" \\
  -H "Authorization: Bearer TOKEN"
```

### 🎯 Performance Testing Scenarios
1. **Concurrent Users**: Simulate 100+ users browsing products
2. **Large Cart**: Add 50+ items to test cart performance  
3. **Search Load**: Perform complex searches with multiple filters
4. **Payment Stress**: Process multiple payments simultaneously
5. **Admin Operations**: Bulk update 1000+ products

### 🔍 Error Handling Tests
- Network timeouts during payment
- Invalid product variants
- Inventory conflicts (overselling)
- Payment provider failures
- Authentication token expiry mid-session
"""


def get_testing_instructions_response(app_name: str) -> openapi.Response:
    """Get testing instructions response for a specific app."""
    instructions_map = {
        "products": TestingInstructions.PRODUCTS_TESTING,
        "authentication": TestingInstructions.AUTHENTICATION_TESTING,
    }

    instructions = instructions_map.get(
        app_name, "Testing instructions not available for this app."
    )

    return openapi.Response(
        description=f"Testing instructions for {app_name.title()} API",
        examples={"text/markdown": instructions},
    )
