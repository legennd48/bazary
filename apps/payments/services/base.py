"""
Base payment service interface.

This module defines the base interface that all payment providers must implement.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, Optional


class PaymentResult:
    """Result of a payment operation."""

    def __init__(
        self,
        success: bool,
        provider_transaction_id: str = "",
        checkout_url: str = "",
        message: str = "",
        error_code: str = "",
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.provider_transaction_id = provider_transaction_id
        self.checkout_url = checkout_url
        self.message = message
        self.error_code = error_code
        self.raw_response = raw_response or {}


class PaymentVerificationResult:
    """Result of a payment verification operation."""

    def __init__(
        self,
        verified: bool,
        status: str = "",
        amount: Decimal = Decimal("0.00"),
        currency: str = "",
        provider_fee: Decimal = Decimal("0.00"),
        message: str = "",
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.verified = verified
        self.status = status
        self.amount = amount
        self.currency = currency
        self.provider_fee = provider_fee
        self.message = message
        self.raw_response = raw_response or {}


class BasePaymentService(ABC):
    """
    Base payment service interface.

    All payment providers must implement this interface to ensure
    consistent behavior across different payment gateways.
    """

    def __init__(self, provider_config: Dict[str, Any]):
        """
        Initialize payment service with provider configuration.

        Args:
            provider_config: Dictionary containing provider configuration
                            including API keys, endpoints, etc.
        """
        self.provider_config = provider_config
        self.api_key = provider_config.get("api_key", "")
        self.secret_key = provider_config.get("secret_key", "")
        self.test_mode = provider_config.get("test_mode", True)
        self.webhook_secret = provider_config.get("webhook_secret", "")

    @abstractmethod
    def initialize_payment(
        self,
        amount: Decimal,
        currency: str,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        tx_ref: str,
        callback_url: str,
        return_url: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """
        Initialize a payment transaction.

        Args:
            amount: Payment amount
            currency: Currency code (e.g., ETB, USD)
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Customer phone number
            tx_ref: Unique transaction reference
            callback_url: URL to receive payment notifications
            return_url: URL to redirect user after payment
            description: Payment description
            metadata: Additional metadata

        Returns:
            PaymentResult object with initialization results
        """
        pass

    @abstractmethod
    def verify_payment(self, tx_ref: str) -> PaymentVerificationResult:
        """
        Verify a payment transaction.

        Args:
            tx_ref: Transaction reference to verify

        Returns:
            PaymentVerificationResult object with verification results
        """
        pass

    @abstractmethod
    def process_webhook(
        self, webhook_data: Dict[str, Any], signature: str = ""
    ) -> Dict[str, Any]:
        """
        Process webhook data from payment provider.

        Args:
            webhook_data: Raw webhook data from provider
            signature: Webhook signature for verification

        Returns:
            Processed webhook data
        """
        pass

    def validate_webhook_signature(
        self, webhook_data: Dict[str, Any], signature: str
    ) -> bool:
        """
        Validate webhook signature for security.

        Args:
            webhook_data: Raw webhook data
            signature: Provided signature

        Returns:
            True if signature is valid, False otherwise
        """
        # Default implementation - should be overridden by providers
        return True

    def format_amount(self, amount: Decimal, currency: str) -> str:
        """
        Format amount according to provider requirements.

        Args:
            amount: Amount to format
            currency: Currency code

        Returns:
            Formatted amount string
        """
        # Default implementation - can be overridden
        return str(amount)

    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number according to provider requirements.

        Args:
            phone_number: Phone number to format

        Returns:
            Formatted phone number
        """
        # Default implementation - can be overridden
        # Remove any non-digit characters and ensure proper format
        cleaned = "".join(filter(str.isdigit, phone_number))

        # Handle Ethiopian phone numbers (should be 10 digits starting with 09 or 07)
        if len(cleaned) == 10 and cleaned.startswith(("09", "07")):
            return cleaned
        elif len(cleaned) == 9 and cleaned.startswith(("9", "7")):
            return "0" + cleaned

        return phone_number  # Return as-is if not Ethiopian format
