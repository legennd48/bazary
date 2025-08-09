"""
Chapa payment service implementation.

This module provides integration with Chapa payment gateway for Ethiopian businesses.
Supports ETB (Ethiopian Birr) and international currencies.
"""

import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings

import requests

from .base import BasePaymentService, PaymentResult, PaymentVerificationResult

logger = logging.getLogger(__name__)


class ChapaPaymentService(BasePaymentService):
    """
    Chapa payment service implementation.

    Provides integration with Chapa's payment API including:
    - Payment initialization
    - Payment verification
    - Webhook processing
    - Ethiopian Birr (ETB) support
    """

    # Chapa API endpoints
    BASE_URL = "https://api.chapa.co/v1"
    ENDPOINTS = {
        "initialize": "/transaction/initialize",
        "verify": "/transaction/verify/{tx_ref}",
    }

    # Supported currencies
    SUPPORTED_CURRENCIES = ["ETB", "USD", "EUR"]

    def __init__(self, provider_config: Dict[str, Any]):
        """Initialize Chapa payment service."""
        super().__init__(provider_config)

        # Chapa-specific configuration
        self.base_url = self.BASE_URL
        if self.test_mode:
            # Use test credentials and endpoints
            logger.info("Chapa service initialized in TEST mode")
        else:
            logger.info("Chapa service initialized in LIVE mode")

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
        Initialize payment with Chapa.

        Creates a payment link that customers can use to complete their payment.
        Supports cards, mobile money, and bank transfers.
        """
        try:
            # Validate inputs
            if currency not in self.SUPPORTED_CURRENCIES:
                return PaymentResult(
                    success=False,
                    message=f"Currency {currency} not supported. Supported: {self.SUPPORTED_CURRENCIES}",
                    error_code="UNSUPPORTED_CURRENCY",
                )

            # Format phone number for Chapa requirements
            formatted_phone = self.format_phone_number(phone_number)

            # Prepare request payload
            payload = {
                "amount": self.format_amount(amount, currency),
                "currency": currency,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": formatted_phone,
                "tx_ref": tx_ref,
                "callback_url": callback_url,
                "return_url": return_url,
                "customization": {
                    "title": "Bazary Payment",
                    "description": description or f"Payment for order {tx_ref}",
                    "logo": getattr(settings, "CHAPA_LOGO_URL", ""),
                },
            }

            # Add metadata if provided
            if metadata:
                payload["meta"] = metadata

            # Make API request
            response = self._make_request("POST", self.ENDPOINTS["initialize"], payload)

            if response.get("status") == "success":
                data = response.get("data", {})
                return PaymentResult(
                    success=True,
                    provider_transaction_id=data.get("tx_ref", tx_ref),
                    checkout_url=data.get("checkout_url", ""),
                    message=response.get("message", "Payment initialized successfully"),
                    raw_response=response,
                )
            else:
                return PaymentResult(
                    success=False,
                    message=response.get("message", "Failed to initialize payment"),
                    error_code="INITIALIZATION_FAILED",
                    raw_response=response,
                )

        except requests.RequestException as e:
            logger.error(f"Chapa API request failed: {str(e)}")
            return PaymentResult(
                success=False,
                message="Payment service temporarily unavailable",
                error_code="API_REQUEST_FAILED",
            )
        except Exception as e:
            logger.error(f"Unexpected error in Chapa payment initialization: {str(e)}")
            return PaymentResult(
                success=False,
                message="An unexpected error occurred",
                error_code="UNEXPECTED_ERROR",
            )

    def verify_payment(self, tx_ref: str) -> PaymentVerificationResult:
        """
        Verify payment status with Chapa.

        Checks the current status of a payment transaction and returns
        detailed information about the payment.
        """
        try:
            # Make verification request
            endpoint = self.ENDPOINTS["verify"].format(tx_ref=tx_ref)
            response = self._make_request("GET", endpoint)

            if response.get("status") == "success":
                data = response.get("data", {})

                # Map Chapa status to our internal status
                chapa_status = data.get("status", "").lower()
                verified = chapa_status == "success"

                # Extract payment details
                amount = Decimal(str(data.get("amount", "0")))
                currency = data.get("currency", "ETB")

                # Calculate provider fee (Chapa charges are usually included in response)
                provider_fee = Decimal(str(data.get("charge", "0")))

                return PaymentVerificationResult(
                    verified=verified,
                    status=chapa_status,
                    amount=amount,
                    currency=currency,
                    provider_fee=provider_fee,
                    message=response.get("message", "Payment verified"),
                    raw_response=response,
                )
            else:
                return PaymentVerificationResult(
                    verified=False,
                    message=response.get("message", "Failed to verify payment"),
                    raw_response=response,
                )

        except requests.RequestException as e:
            logger.error(f"Chapa verification request failed: {str(e)}")
            return PaymentVerificationResult(
                verified=False,
                message="Verification service temporarily unavailable",
            )
        except Exception as e:
            logger.error(f"Unexpected error in Chapa payment verification: {str(e)}")
            return PaymentVerificationResult(
                verified=False,
                message="An unexpected error occurred during verification",
            )

    def process_webhook(
        self, webhook_data: Dict[str, Any], signature: str = ""
    ) -> Dict[str, Any]:
        """
        Process webhook notification from Chapa.

        Handles real-time payment status updates sent by Chapa
        when payment status changes.
        """
        try:
            # Validate webhook signature if provided
            if signature and not self.validate_webhook_signature(
                webhook_data, signature
            ):
                logger.warning("Invalid Chapa webhook signature")
                return {"valid": False, "error": "Invalid signature"}

            # Extract webhook data
            tx_ref = webhook_data.get("trx_ref", "")
            ref_id = webhook_data.get("ref_id", "")
            status = webhook_data.get("status", "").lower()

            # Verify the payment to get complete details
            verification_result = self.verify_payment(tx_ref)

            processed_data = {
                "valid": True,
                "tx_ref": tx_ref,
                "ref_id": ref_id,
                "status": status,
                "verified": verification_result.verified,
                "verification_data": verification_result.raw_response,
                "raw_webhook": webhook_data,
            }

            logger.info(f"Processed Chapa webhook for transaction {tx_ref}: {status}")
            return processed_data

        except Exception as e:
            logger.error(f"Error processing Chapa webhook: {str(e)}")
            return {"valid": False, "error": str(e)}

    def validate_webhook_signature(
        self, webhook_data: Dict[str, Any], signature: str
    ) -> bool:
        """
        Validate Chapa webhook signature.

        Chapa uses HMAC-SHA256 for webhook signature validation.
        """
        if not self.webhook_secret or not signature:
            return True  # Skip validation if no secret configured

        try:
            # Create expected signature
            payload = json.dumps(webhook_data, sort_keys=True)
            expected_signature = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)

        except Exception as e:
            logger.error(f"Error validating Chapa webhook signature: {str(e)}")
            return False

    def format_amount(self, amount: Decimal, currency: str) -> str:
        """
        Format amount for Chapa API.

        Chapa expects amounts as string with proper decimal places.
        """
        if currency == "ETB":
            # Ethiopian Birr - typically 2 decimal places
            return f"{amount:.2f}"
        else:
            # Other currencies - use 2 decimal places
            return f"{amount:.2f}"

    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for Chapa API.

        Chapa requires Ethiopian phone numbers in 09xxxxxxxx or 07xxxxxxxx format.
        """
        # Remove any non-digit characters
        cleaned = "".join(filter(str.isdigit, phone_number))

        # Handle Ethiopian phone numbers
        if len(cleaned) == 10 and cleaned.startswith(("09", "07")):
            return cleaned
        elif len(cleaned) == 9 and cleaned.startswith(("9", "7")):
            return "0" + cleaned
        elif len(cleaned) == 12 and cleaned.startswith("251"):
            # Convert international format (+251) to local format
            local_part = cleaned[3:]
            if len(local_part) == 9 and local_part.startswith(("9", "7")):
                return "0" + local_part

        # Return original if no specific formatting needed
        return phone_number

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Chapa API.

        Handles authentication, error handling, and response parsing.
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
            "User-Agent": "Bazary-Ecommerce/1.0",
        }

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Log request for debugging (without sensitive data)
            logger.info(f"Chapa API {method} {endpoint}: {response.status_code}")

            # Handle HTTP errors
            response.raise_for_status()

            # Parse JSON response
            response_data = response.json()

            return response_data

        except requests.exceptions.Timeout:
            logger.error(f"Chapa API timeout for {method} {endpoint}")
            raise requests.RequestException("Request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Chapa API request error: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Chapa API response: {str(e)}")
            raise requests.RequestException("Invalid JSON response")

    def get_supported_payment_methods(self) -> Dict[str, Any]:
        """
        Get supported payment methods for Chapa.

        Returns information about available payment options.
        """
        return {
            "cards": {
                "supported": True,
                "types": ["visa", "mastercard", "american_express"],
                "description": "Credit and debit cards",
            },
            "mobile_money": {
                "supported": True,
                "providers": ["telebirr", "cbe_birr", "amole", "hello_cash"],
                "description": "Ethiopian mobile money services",
            },
            "bank_transfer": {
                "supported": True,
                "description": "Direct bank transfers",
            },
            "cash": {
                "supported": False,
                "description": "Cash payments not supported online",
            },
        }

    def get_transaction_fees(
        self, amount: Decimal, currency: str
    ) -> Dict[str, Decimal]:
        """
        Calculate Chapa transaction fees.

        Note: Actual fees depend on your Chapa merchant agreement.
        This is a general estimation.
        """
        if currency == "ETB":
            # Ethiopian Birr fees (example rates)
            if amount <= Decimal("100"):
                fee = Decimal("3.00")  # Minimum fee
            else:
                fee = amount * Decimal("0.025")  # 2.5% fee
                fee = min(fee, Decimal("500.00"))  # Maximum fee cap
        else:
            # International currency fees
            fee = amount * Decimal("0.035")  # 3.5% fee
            fee = max(fee, Decimal("5.00"))  # Minimum fee

        return {
            "provider_fee": fee,
            "customer_fee": Decimal("0.00"),  # Merchant absorbs fees
            "total_fee": fee,
        }
