"""
Security middleware for API protection.
"""

import logging
import re
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """

    def process_response(self, request, response):
        """Add security headers to the response."""

        # Content Security Policy
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self';"
        )

        # X-Frame-Options
        response["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        response["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Only add HSTS in production with HTTPS
        if not settings.DEBUG and request.is_secure():
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class IPWhitelistMiddleware(MiddlewareMixin):
    """
    Middleware to restrict access to whitelisted IP addresses.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = getattr(settings, "IP_WHITELIST", [])
        self.admin_whitelist = getattr(settings, "ADMIN_IP_WHITELIST", [])
        super().__init__(get_response)

    def process_request(self, request):
        """Check if IP is whitelisted for admin access."""
        if not self.admin_whitelist:
            return None

        # Only apply to admin URLs
        if not request.path.startswith("/admin/"):
            return None

        client_ip = self.get_client_ip(request)

        if client_ip not in self.admin_whitelist:
            logger.warning(f"Blocked admin access from non-whitelisted IP: {client_ip}")
            return JsonResponse(
                {
                    "error": "Access denied",
                    "message": "Your IP address is not authorized for admin access",
                },
                status=403,
            )

        return None

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class RequestSanitizationMiddleware(MiddlewareMixin):
    """
    Middleware to sanitize incoming requests.
    """

    # Patterns for potential security threats
    XSS_PATTERNS = [
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"vbscript:", re.IGNORECASE),
        re.compile(r"onload=", re.IGNORECASE),
        re.compile(r"onerror=", re.IGNORECASE),
        re.compile(r"onclick=", re.IGNORECASE),
    ]

    SQL_INJECTION_PATTERNS = [
        re.compile(
            r"(\w*)((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))", re.IGNORECASE
        ),
        re.compile(r"union.*?select", re.IGNORECASE),
        re.compile(r"select.*?from", re.IGNORECASE),
        re.compile(r"insert.*?into", re.IGNORECASE),
        re.compile(r"delete.*?from", re.IGNORECASE),
        re.compile(r"drop.*?table", re.IGNORECASE),
    ]

    def process_request(self, request):
        """Sanitize request data."""
        # Skip for certain content types
        if request.content_type == "application/json":
            return None

        # Check query parameters
        if self.contains_malicious_content(str(request.GET)):
            logger.warning(
                f"Blocked request with malicious query params from {self.get_client_ip(request)}"
            )
            return JsonResponse(
                {
                    "error": "Invalid request",
                    "message": "Request contains potentially malicious content",
                },
                status=400,
            )

        # Check POST data
        if hasattr(request, "POST") and self.contains_malicious_content(
            str(request.POST)
        ):
            logger.warning(
                f"Blocked request with malicious POST data from {self.get_client_ip(request)}"
            )
            return JsonResponse(
                {
                    "error": "Invalid request",
                    "message": "Request contains potentially malicious content",
                },
                status=400,
            )

        return None

    def contains_malicious_content(self, data):
        """Check if data contains malicious patterns."""
        # Check for XSS patterns
        for pattern in self.XSS_PATTERNS:
            if pattern.search(data):
                return True

        # Check for SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(data):
                return True

        return False

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class APISecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-related events.
    """

    def process_request(self, request):
        """Log request details for security monitoring."""
        # Only log API requests
        if not request.path.startswith("/api/"):
            return None

        # Log failed authentication attempts
        if hasattr(request, "user") and not request.user.is_authenticated:
            if "Authorization" in request.headers:
                logger.warning(
                    f"Failed authentication attempt from {self.get_client_ip(request)} to {request.path}"
                )

        # Log admin access attempts
        if request.path.startswith("/api/v1/auth/users/") and request.method in [
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        ]:
            logger.info(
                f"Admin operation attempt: {request.method} {request.path} from {self.get_client_ip(request)}"
            )

        return None

    def process_response(self, request, response):
        """Log response details for security monitoring."""
        # Log failed requests
        if response.status_code >= 400:
            logger.warning(
                f"Failed request: {request.method} {request.path} - {response.status_code} from {self.get_client_ip(request)}"
            )

        return response

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
