"""
Payment service factory.

This module provides a factory for creating payment service instances
based on provider configuration.
"""

import logging
from typing import Any, Dict, Optional

from django.core.exceptions import ImproperlyConfigured

from .base import BasePaymentService
from .chapa import ChapaPaymentService

logger = logging.getLogger(__name__)


class PaymentServiceFactory:
    """
    Factory for creating payment service instances.

    Manages different payment providers and creates appropriate
    service instances based on provider type.
    """

    # Registry of available payment services
    SERVICES = {
        "chapa": ChapaPaymentService,
        # Add other providers here as they are implemented
        # "stripe": StripePaymentService,
        # "paypal": PayPalPaymentService,
    }

    @classmethod
    def create_service(
        self, provider_type: str, provider_config: Dict[str, Any]
    ) -> BasePaymentService:
        """
        Create payment service instance.

        Args:
            provider_type: Type of payment provider (e.g., 'chapa', 'stripe')
            provider_config: Provider configuration including API keys

        Returns:
            Payment service instance

        Raises:
            ImproperlyConfigured: If provider type is not supported
        """
        if provider_type not in self.SERVICES:
            available_providers = ", ".join(self.SERVICES.keys())
            raise ImproperlyConfigured(
                f"Unsupported payment provider '{provider_type}'. "
                f"Available providers: {available_providers}"
            )

        service_class = self.SERVICES[provider_type]

        try:
            service = service_class(provider_config)
            logger.info(f"Created {provider_type} payment service")
            return service
        except Exception as e:
            logger.error(f"Failed to create {provider_type} payment service: {str(e)}")
            raise ImproperlyConfigured(
                f"Failed to initialize {provider_type} payment service: {str(e)}"
            )

    @classmethod
    def get_available_providers(self) -> Dict[str, str]:
        """
        Get list of available payment providers.

        Returns:
            Dictionary mapping provider types to service class names
        """
        return {
            provider_type: service_class.__name__
            for provider_type, service_class in self.SERVICES.items()
        }

    @classmethod
    def register_service(self, provider_type: str, service_class: type) -> None:
        """
        Register a new payment service.

        Args:
            provider_type: Provider type identifier
            service_class: Service class implementing BasePaymentService
        """
        if not issubclass(service_class, BasePaymentService):
            raise ValueError(f"Service class must inherit from BasePaymentService")

        self.SERVICES[provider_type] = service_class
        logger.info(f"Registered payment service: {provider_type}")


def get_payment_service(
    provider_type: str, provider_config: Dict[str, Any]
) -> BasePaymentService:
    """
    Convenience function to get payment service instance.

    Args:
        provider_type: Type of payment provider
        provider_config: Provider configuration

    Returns:
        Payment service instance
    """
    return PaymentServiceFactory.create_service(provider_type, provider_config)


def get_payment_service_from_provider(provider) -> BasePaymentService:
    """
    Get payment service from PaymentProvider model instance.

    Args:
        provider: PaymentProvider model instance

    Returns:
        Payment service instance
    """
    config = {
        "api_key": provider.api_key,
        "secret_key": provider.secret_key,
        "webhook_secret": provider.webhook_secret,
        "test_mode": provider.test_mode,
        "supported_currencies": provider.supported_currencies,
        "configuration": provider.configuration,
    }

    return get_payment_service(provider.provider_type, config)
