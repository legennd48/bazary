"""
Custom throttling classes for API rate limiting.
"""

from rest_framework.throttling import (
    UserRateThrottle,
    AnonRateThrottle,
    ScopedRateThrottle,
)
from django.core.cache import cache
import time


class BurstRateThrottle(UserRateThrottle):
    """
    Throttle for burst requests - high frequency, short duration.
    """

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """
    Throttle for sustained requests - lower frequency, longer duration.
    """

    scope = "sustained"


class LoginRateThrottle(ScopedRateThrottle):
    """
    Throttle for login attempts to prevent brute force attacks.
    """

    scope = "login"

    def get_cache_key(self, request, view):
        """
        Include IP address in the cache key for login attempts.
        """
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class RegistrationRateThrottle(ScopedRateThrottle):
    """
    Throttle for registration attempts to prevent spam accounts.
    """

    scope = "registration"


class AdminRateThrottle(UserRateThrottle):
    """
    Higher rate limits for admin users.
    """

    scope = "admin"

    def allow_request(self, request, view):
        """
        Admin users get higher rate limits.
        """
        if request.user.is_authenticated and request.user.is_staff:
            return True
        return super().allow_request(request, view)


class AnonymousThrottle(AnonRateThrottle):
    """
    Throttle for anonymous users with conservative limits.
    """

    scope = "anon"


class SearchRateThrottle(ScopedRateThrottle):
    """
    Throttle for search operations to prevent abuse.
    """

    scope = "search"


class APIKeyThrottle(UserRateThrottle):
    """
    Throttle for API key based access (future implementation).
    """

    scope = "api_key"

    def get_cache_key(self, request, view):
        """
        Use API key as identifier instead of user ID.
        """
        api_key = request.META.get("HTTP_X_API_KEY")
        if api_key:
            return self.cache_format % {"scope": self.scope, "ident": api_key}
        return super().get_cache_key(request, view)


class DynamicRateThrottle(UserRateThrottle):
    """
    Dynamic throttle that adjusts based on system load.
    """

    def __init__(self):
        super().__init__()
        self.base_rate = self.rate

    def allow_request(self, request, view):
        """
        Adjust rate based on current system load.
        """
        # Get current system load indicator (could be from monitoring)
        load_factor = cache.get("system_load_factor", 1.0)

        # Adjust rate based on load (higher load = lower rate limits)
        if load_factor > 1.5:
            self.rate = f"{int(float(self.base_rate.split('/')[0]) * 0.5)}/{self.base_rate.split('/')[1]}"
        elif load_factor > 1.2:
            self.rate = f"{int(float(self.base_rate.split('/')[0]) * 0.7)}/{self.base_rate.split('/')[1]}"
        else:
            self.rate = self.base_rate

        return super().allow_request(request, view)
