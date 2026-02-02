"""
Core views package.
"""

from .health import health_check
from .platform import (
    PlatformCapabilitiesView,
    PlatformConfigView,
    PlatformHealthView,
)

__all__ = [
    "health_check",
    "PlatformCapabilitiesView",
    "PlatformConfigView",
    "PlatformHealthView",
]
