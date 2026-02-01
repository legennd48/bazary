"""Services app configuration."""

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    """Configuration for the Services app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.services"
    verbose_name = "Services & Offerings"
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            from . import signals  # noqa: F401
        except ImportError:
            pass
