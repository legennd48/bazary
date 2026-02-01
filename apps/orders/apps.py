"""Orders app configuration."""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """Configuration for the Orders app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.orders"
    verbose_name = "Orders & Checkout"
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
