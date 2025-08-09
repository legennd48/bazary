"""
Payment app configuration.

This module configures the payments Django app for the bazary e-commerce platform.
"""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configuration for the payments app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Payments'
    
    def ready(self):
        """App initialization - import signals and other setup."""
        pass  # Import signals here when needed
