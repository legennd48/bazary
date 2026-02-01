"""
Capability Registry Implementation.

This module implements the core capability registry that controls
which platform features are enabled per deployment.

Design principles:
- Capabilities are explicitly configured (no implicit enablement)
- Disabled capabilities have zero attack surface (no routes, permissions, etc.)
- Configuration is centralized and validated at startup
- Multi-client deployments differ only by configuration, not code
"""

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class Capability:
    """
    Definition of a platform capability.
    
    Attributes:
        name: Unique identifier for the capability (e.g., 'products', 'services')
        display_name: Human-readable name for admin/UI
        description: What this capability provides
        django_apps: List of Django apps to install when enabled
        dependencies: Other capabilities this one requires
        default_enabled: Whether enabled by default (conservative: False)
    """
    name: str
    display_name: str
    description: str
    django_apps: tuple = field(default_factory=tuple)
    dependencies: tuple = field(default_factory=tuple)
    default_enabled: bool = False
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Capability):
            return self.name == other.name
        return False


# Define all platform capabilities
CAPABILITY_DEFINITIONS: Dict[str, Capability] = {}


def register_capability(
    name: str,
    display_name: str,
    description: str,
    django_apps: tuple = (),
    dependencies: tuple = (),
    default_enabled: bool = False,
) -> Capability:
    """Register a capability definition."""
    cap = Capability(
        name=name,
        display_name=display_name,
        description=description,
        django_apps=django_apps,
        dependencies=dependencies,
        default_enabled=default_enabled,
    )
    CAPABILITY_DEFINITIONS[name] = cap
    return cap


# ============================================================================
# CORE CAPABILITIES (always available, cannot be disabled)
# ============================================================================

CORE = register_capability(
    name="core",
    display_name="Core Platform",
    description="Core platform infrastructure: auth, users, base models, utilities",
    django_apps=(
        "apps.core",
        "apps.authentication",
    ),
    default_enabled=True,
)

# ============================================================================
# COMMERCE CAPABILITIES (optional, per-client)
# ============================================================================

PRODUCTS = register_capability(
    name="products",
    display_name="Products & Catalog",
    description=(
        "Physical and digital product catalog with Shopify-level variants, "
        "categories, tags, inventory tracking, and media management"
    ),
    django_apps=(
        "apps.categories",
        "apps.products",
    ),
    dependencies=("core",),
    default_enabled=False,
)

SERVICES = register_capability(
    name="services",
    display_name="Service Offerings",
    description=(
        "Service catalog with duration-based pricing, provider assignment, "
        "and service-specific policies"
    ),
    django_apps=(
        "apps.services",
    ),
    dependencies=("core",),
    default_enabled=False,
)

BOOKINGS = register_capability(
    name="bookings",
    display_name="Bookings & Reservations",
    description=(
        "Time-based reservation system with availability slots, "
        "conflict prevention, and booking lifecycle management"
    ),
    django_apps=(
        "apps.bookings",
    ),
    dependencies=("core",),
    default_enabled=False,
)

ORDERS = register_capability(
    name="orders",
    display_name="Orders & Checkout",
    description=(
        "Order management, checkout workflows, and fulfillment tracking"
    ),
    django_apps=(
        "apps.orders",
    ),
    dependencies=("core",),
    default_enabled=False,
)

PAYMENTS = register_capability(
    name="payments",
    display_name="Payment Processing",
    description=(
        "Multi-gateway payment processing, transactions, refunds, and webhooks"
    ),
    django_apps=(
        "apps.payments",
    ),
    dependencies=("core", "orders"),
    default_enabled=False,
)

NOTIFICATIONS = register_capability(
    name="notifications",
    display_name="Notifications",
    description=(
        "Real-time WebSocket notifications and async email/SMS delivery"
    ),
    django_apps=(
        "apps.notifications",
    ),
    dependencies=("core",),
    default_enabled=False,
)


class CapabilityRegistry:
    """
    Central registry for platform capabilities.
    
    Reads enabled capabilities from Django settings and provides
    runtime checks for capability-gated functionality.
    """
    
    _instance: Optional["CapabilityRegistry"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "CapabilityRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._definitions: Dict[str, Capability] = CAPABILITY_DEFINITIONS.copy()
        self._enabled: Set[str] = set()
        self._initialized = True
    
    def configure(self, enabled_capabilities: List[str]) -> None:
        """
        Configure which capabilities are enabled.
        
        Called during Django startup from settings.
        Validates dependencies and prevents invalid configurations.
        """
        # Always enable core
        self._enabled = {"core"}
        
        # Add explicitly enabled capabilities
        for cap_name in enabled_capabilities:
            if cap_name not in self._definitions:
                raise ImproperlyConfigured(
                    f"Unknown capability '{cap_name}'. "
                    f"Available: {list(self._definitions.keys())}"
                )
            self._enabled.add(cap_name)
        
        # Resolve dependencies (add required capabilities)
        self._resolve_dependencies()
        
        # Validate the final configuration
        self._validate()
    
    def _resolve_dependencies(self) -> None:
        """Add capabilities required by enabled ones."""
        changed = True
        while changed:
            changed = False
            for cap_name in list(self._enabled):
                cap = self._definitions[cap_name]
                for dep_name in cap.dependencies:
                    if dep_name not in self._enabled:
                        self._enabled.add(dep_name)
                        changed = True
    
    def _validate(self) -> None:
        """Validate the capability configuration."""
        for cap_name in self._enabled:
            cap = self._definitions[cap_name]
            for dep_name in cap.dependencies:
                if dep_name not in self._enabled:
                    raise ImproperlyConfigured(
                        f"Capability '{cap_name}' requires '{dep_name}' "
                        f"but it is not enabled"
                    )
    
    def is_enabled(self, capability_name: str) -> bool:
        """Check if a capability is enabled."""
        return capability_name in self._enabled
    
    def get_enabled(self) -> FrozenSet[str]:
        """Get all enabled capability names."""
        return frozenset(self._enabled)
    
    def get_enabled_capabilities(self) -> List[Capability]:
        """Get all enabled capability definitions."""
        return [
            self._definitions[name]
            for name in sorted(self._enabled)
        ]
    
    def any_enabled(self, *capability_names: str) -> bool:
        """Check if any of the given capabilities are enabled."""
        return any(name in self._enabled for name in capability_names)
    
    def all_enabled(self, *capability_names: str) -> bool:
        """Check if all of the given capabilities are enabled."""
        return all(name in self._enabled for name in capability_names)
    
    def get_installed_apps(self) -> List[str]:
        """
        Get Django apps to install based on enabled capabilities.
        
        Returns apps in dependency order.
        """
        apps: List[str] = []
        seen: Set[str] = set()
        
        # Process in dependency order
        for cap in self.get_enabled_capabilities():
            for app in cap.django_apps:
                if app not in seen:
                    apps.append(app)
                    seen.add(app)
        
        return apps
    
    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability definition by name."""
        return self._definitions.get(name)
    
    def register(self, capability: Capability) -> None:
        """Register a new capability (for extensibility)."""
        self._definitions[capability.name] = capability
    
    def get_capability_info(self) -> Dict[str, Any]:
        """
        Get capability information for API exposure.
        
        Used by the /api/platform/capabilities endpoint.
        """
        return {
            "enabled": list(self._enabled),
            "available": [
                {
                    "name": cap.name,
                    "display_name": cap.display_name,
                    "description": cap.description,
                    "enabled": cap.name in self._enabled,
                    "dependencies": list(cap.dependencies),
                }
                for cap in self._definitions.values()
            ],
        }


# Singleton instance
capabilities = CapabilityRegistry()


def require_capability(*required_capabilities: str) -> Callable:
    """
    Decorator to require capabilities for a view/function.
    
    Usage:
        @require_capability('products')
        def my_view(request):
            ...
        
        @require_capability('services', 'bookings')  # Requires both
        class MyViewSet(ViewSet):
            ...
    """
    def decorator(func_or_class: Callable) -> Callable:
        if isinstance(func_or_class, type):
            # Class-based view
            original_dispatch = func_or_class.dispatch
            
            @wraps(original_dispatch)
            def dispatch(self, request, *args, **kwargs):
                for cap in required_capabilities:
                    if not capabilities.is_enabled(cap):
                        from rest_framework.response import Response
                        from rest_framework import status
                        return Response(
                            {
                                "error": "capability_disabled",
                                "message": f"The '{cap}' capability is not enabled",
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )
                return original_dispatch(self, request, *args, **kwargs)
            
            func_or_class.dispatch = dispatch
            return func_or_class
        else:
            # Function-based view
            @wraps(func_or_class)
            def wrapper(*args, **kwargs):
                for cap in required_capabilities:
                    if not capabilities.is_enabled(cap):
                        from rest_framework.response import Response
                        from rest_framework import status
                        return Response(
                            {
                                "error": "capability_disabled",
                                "message": f"The '{cap}' capability is not enabled",
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )
                return func_or_class(*args, **kwargs)
            return wrapper
    
    return decorator
