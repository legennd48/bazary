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
