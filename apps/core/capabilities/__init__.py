"""
Bazary Capability Registry System.

This module provides centralized capability management for the platform,
enabling per-deployment configuration of which features are available.

Capabilities control:
- Which Django apps are installed
- Which URL routes are registered
- Which permissions are available
- Which admin sections are visible
- Which background tasks run
- Which signals are connected

Usage:
    from apps.core.capabilities import capabilities
    
    if capabilities.is_enabled('products'):
        # Do product-specific work
        pass
    
    # Get all enabled capabilities
    enabled = capabilities.get_enabled()
    
    # Check multiple capabilities
    if capabilities.any_enabled('services', 'bookings'):
        # At least one is enabled
        pass
"""

from .registry import (
    Capability,
    CapabilityRegistry,
    capabilities,
    require_capability,
)

__all__ = [
    "Capability",
    "CapabilityRegistry",
    "capabilities",
    "require_capability",
]
