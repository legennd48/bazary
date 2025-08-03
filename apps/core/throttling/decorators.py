"""
Rate limiting decorators for view functions and classes.
"""

from functools import wraps

from django.http import JsonResponse

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.response import Response


def api_ratelimit(group=None, key="ip", rate="60/h", method="ALL", block=True):
    """
    Rate limiting decorator for API views.

    Args:
        group: String identifying the rate limit group
        key: What to use as the rate limit key (ip, user, header, etc.)
        rate: Rate limit format (e.g., '60/h', '10/m')
        method: HTTP methods to apply rate limiting to
        block: Whether to block requests that exceed the limit
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Apply django-ratelimit
            limited_view = ratelimit(
                group=group, key=key, rate=rate, method=method, block=block
            )(view_func)

            # Check if request was rate limited
            if hasattr(request, "limited") and request.limited:
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Rate limit: {rate}",
                        "retry_after": 3600 if "h" in rate else 60,
                    },
                    status=429,
                )

            return limited_view(request, *args, **kwargs)

        return wrapped_view

    return decorator


def login_ratelimit(rate="5/m"):
    """
    Rate limiting decorator specifically for login views.
    """
    return api_ratelimit(group="login", key="ip", rate=rate, method="POST", block=True)


def registration_ratelimit(rate="3/h"):
    """
    Rate limiting decorator specifically for registration views.
    """
    return api_ratelimit(
        group="registration", key="ip", rate=rate, method="POST", block=True
    )


def search_ratelimit(rate="30/m"):
    """
    Rate limiting decorator for search operations.
    """
    return api_ratelimit(
        group="search", key="user_or_ip", rate=rate, method="GET", block=True
    )


def admin_ratelimit(rate="100/h"):
    """
    Rate limiting decorator for admin operations.
    """
    return api_ratelimit(group="admin", key="user", rate=rate, method="ALL", block=True)


def api_key_ratelimit(rate="1000/h"):
    """
    Rate limiting decorator for API key based access.
    """

    def key_func(group, request):
        """Use API key as the rate limit key."""
        return request.META.get("HTTP_X_API_KEY", request.META.get("REMOTE_ADDR"))

    return api_ratelimit(
        group="api_key", key=key_func, rate=rate, method="ALL", block=True
    )


class RateLimitMixin:
    """
    Mixin to add rate limiting to DRF ViewSets.
    """

    rate_limit_rules = {
        "list": "60/h",
        "create": "20/h",
        "update": "30/h",
        "destroy": "10/h",
        "retrieve": "100/h",
    }

    def dispatch(self, request, *args, **kwargs):
        """Apply rate limiting based on the action."""
        if hasattr(self, "action") and self.action in self.rate_limit_rules:
            rate = self.rate_limit_rules[self.action]

            # Apply rate limiting
            from django_ratelimit.core import is_ratelimited

            ratelimited = is_ratelimited(
                request=request,
                group=f"{self.__class__.__name__.lower()}_{self.action}",
                fn=lambda req: (
                    req.user.id
                    if req.user.is_authenticated
                    else req.META.get("REMOTE_ADDR")
                ),
                rate=rate,
                increment=True,
            )

            if ratelimited:
                return Response(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Too many {self.action} requests. Rate limit: {rate}",
                        "retry_after": 3600 if "h" in rate else 60,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        return super().dispatch(request, *args, **kwargs)


# Convenience decorators for common patterns
def user_rate_limit(rate="60/h"):
    """Rate limit based on authenticated user."""
    return api_ratelimit(key="user", rate=rate)


def ip_rate_limit(rate="30/h"):
    """Rate limit based on IP address."""
    return api_ratelimit(key="ip", rate=rate)


def header_rate_limit(header="X-Forwarded-For", rate="60/h"):
    """Rate limit based on a specific header."""

    def key_func(group, request):
        return request.META.get(
            f'HTTP_{header.upper().replace("-", "_")}', request.META.get("REMOTE_ADDR")
        )

    return api_ratelimit(key=key_func, rate=rate)
