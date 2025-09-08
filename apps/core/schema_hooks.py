"""
Custom schema hooks for DRF Spectacular.

This module contains post-processing hooks to tweak the generated OpenAPI schema.
"""

from typing import Any, Dict


def rename_api_tag_to_z_advanced(
    result: Dict[str, Any], generator: Any, request: Any, **kwargs
) -> Dict[str, Any]:
    """Rename any 'api' tag to 'Z Advanced Features' so it appears at the end of UI.

    This primarily affects router root endpoints and any views that defaulted to the
    generic 'api' tag.
    """
    if not result:
        return result

    paths = result.get("paths") or {}
    for _, path_item in paths.items():
        # path_item may include operations: get, post, put, patch, delete, options, head
        for op in ("get", "post", "put", "patch", "delete", "options", "head"):
            operation = path_item.get(op)
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or []
            if not tags:
                continue
            # Replace any occurrence of 'api'
            new_tags = ["Z Advanced Features" if t == "api" else t for t in tags]
            operation["tags"] = new_tags

    # Also adjust top-level tags metadata if present
    if "tags" in result and isinstance(result["tags"], list):
        for tag in result["tags"]:
            if isinstance(tag, dict) and tag.get("name") == "api":
                tag["name"] = "Z Advanced Features"

    return result


def normalize_and_canonicalize_tags(
    result: Dict[str, Any], generator: Any, request: Any, **kwargs
) -> Dict[str, Any]:
    """Normalize operation tags to the canonical emoji-tagged groups.

    This prevents clients (e.g., Insomnia) from showing duplicate/non-icon groups
    like "Products" vs "13 📦 Products" or lowercase variants.
    """
    if not result:
        return result

    # Import lazily to avoid circulars
    from apps.core.swagger_docs import SwaggerTags

    # map lowercased simple names to canonical emoji-tagged names
    CANONICAL: Dict[str, str] = {
        "authentication": SwaggerTags.AUTHENTICATION,
        "auth": SwaggerTags.AUTHENTICATION,
        "email verification": SwaggerTags.EMAIL_VERIFICATION,
        "password management": SwaggerTags.PASSWORD_MANAGEMENT,
        "token management": SwaggerTags.TOKEN_MANAGEMENT,
        "user profile": SwaggerTags.USER_PROFILE,
        "user addresses": SwaggerTags.USER_ADDRESSES,
        "user activity": SwaggerTags.USER_ACTIVITY,
        "admin - user management": SwaggerTags.ADMIN_USER_MANAGEMENT,
        "admin user management": SwaggerTags.ADMIN_USER_MANAGEMENT,
        "admin - product management": SwaggerTags.ADMIN_PRODUCT_MANAGEMENT,
        "categories": SwaggerTags.CATEGORIES,
        "category": SwaggerTags.CATEGORIES,
        "tags": SwaggerTags.TAGS,
        "tag": SwaggerTags.TAGS,
        "products": SwaggerTags.PRODUCTS,
        "product": SwaggerTags.PRODUCTS,
        "product variants": SwaggerTags.PRODUCT_VARIANTS,
        "variant options": SwaggerTags.VARIANT_OPTIONS,
        "product images": SwaggerTags.PRODUCT_IMAGES,
        "product discovery": SwaggerTags.PRODUCT_DISCOVERY,
        "search": SwaggerTags.PRODUCT_SEARCH,
        "search & filters": SwaggerTags.PRODUCT_SEARCH,
        "shopping cart": SwaggerTags.SHOPPING_CART,
        "cart management": SwaggerTags.CART_MANAGEMENT,
        "payment providers": SwaggerTags.PAYMENT_PROVIDERS,
        "payment methods": SwaggerTags.PAYMENT_METHODS,
        "transactions": SwaggerTags.TRANSACTIONS,
        "transaction": SwaggerTags.TRANSACTIONS,
        "payment webhooks": SwaggerTags.PAYMENT_WEBHOOKS,
    "system health": SwaggerTags.SYSTEM_HEALTH,
    "health": SwaggerTags.SYSTEM_HEALTH,
    "health check": SwaggerTags.SYSTEM_HEALTH,
    "healthcheck": SwaggerTags.SYSTEM_HEALTH,
        "api testing": SwaggerTags.API_TESTING,
        "testing guides": SwaggerTags.TESTING_GUIDES,
    }

    paths = result.get("paths") or {}
    for path, path_item in paths.items():
        for op in ("get", "post", "put", "patch", "delete", "options", "head"):
            operation = path_item.get(op)
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags") or []
            if not tags:
                continue
            updated = []
            for t in tags:
                if not isinstance(t, str):
                    updated.append(t)
                    continue
                key = t.strip().lower()
                canonical = CANONICAL.get(key)

                # Context-aware remapping for generic 'payments' tag by URL path
                if not canonical and key == "payments":
                    if path.startswith("/api/v1/payments/carts"):
                        canonical = SwaggerTags.SHOPPING_CART
                    elif path.startswith("/api/v1/payments/methods"):
                        canonical = SwaggerTags.PAYMENT_METHODS
                    elif path.startswith("/api/v1/payments/providers"):
                        canonical = SwaggerTags.PAYMENT_PROVIDERS
                    elif path.startswith("/api/v1/payments/transactions"):
                        canonical = SwaggerTags.TRANSACTIONS
                    elif (
                        path.startswith("/api/v1/payments/webhooks")
                        or path.startswith("/api/v1/payments/callbacks")
                        or "/webhook" in path
                        or "/callback" in path
                    ):
                        canonical = SwaggerTags.PAYMENT_WEBHOOKS

                updated.append(canonical or t)
            operation["tags"] = updated

    # Optionally, we could sync top-level tags metadata; leave as-is to avoid surprises
    return result
