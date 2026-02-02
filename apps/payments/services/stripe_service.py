"""
Stripe Payment Service.

Full Stripe integration with:
- Payment intents for secure payments
- Idempotency key support to prevent duplicate charges
- Webhook handling for async events
- Refund processing
- Payment method management
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import stripe
from django.conf import settings

from .base import BasePaymentService, PaymentResult, PaymentVerificationResult

logger = logging.getLogger(__name__)


class StripePaymentService(BasePaymentService):
    """
    Stripe payment service implementation.
    
    Implements the BasePaymentService interface for Stripe.
    Supports Payment Intents API for SCA compliance.
    """
    
    def __init__(self, provider_config: Dict[str, Any]):
        """Initialize Stripe service with configuration."""
        super().__init__(provider_config)
        
        # Set Stripe API key
        stripe.api_key = self.secret_key
        
        # Optional: Set API version for stability
        stripe.api_version = provider_config.get("api_version", "2024-12-18.acacia")
        
        self.webhook_secret = provider_config.get("webhook_secret", "")
        self.currency = provider_config.get("default_currency", "USD").lower()
    
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
        idempotency_key: Optional[str] = None,
    ) -> PaymentResult:
        """
        Initialize a Stripe Payment Intent.
        
        Uses idempotency keys to prevent duplicate charges on retries.
        
        Args:
            amount: Payment amount in major currency unit (e.g., 10.00)
            currency: Currency code (e.g., USD)
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Customer phone
            tx_ref: Unique transaction reference (used as idempotency key if not provided)
            callback_url: Webhook URL for payment events
            return_url: URL to redirect after payment
            description: Payment description
            metadata: Additional metadata
            idempotency_key: Unique key for idempotency (defaults to tx_ref)
            
        Returns:
            PaymentResult with client_secret for frontend
        """
        try:
            # Convert to smallest currency unit (cents)
            amount_cents = int(amount * 100)
            
            # Use tx_ref as idempotency key if not provided
            idem_key = idempotency_key or f"pi_{tx_ref}"
            
            # Check if customer exists
            customer = self._get_or_create_customer(
                email=email,
                name=f"{first_name} {last_name}",
                phone=phone_number,
            )
            
            # Create Payment Intent with idempotency key
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer.id,
                description=description or f"Order {tx_ref}",
                metadata={
                    "tx_ref": tx_ref,
                    "email": email,
                    **(metadata or {}),
                },
                receipt_email=email,
                automatic_payment_methods={
                    "enabled": True,
                },
                # These are critical for the hosted checkout flow
                return_url=return_url,
                idempotency_key=idem_key,
            )
            
            logger.info(f"Created Stripe PaymentIntent: {intent.id} for {tx_ref}")
            
            return PaymentResult(
                success=True,
                provider_transaction_id=intent.id,
                checkout_url="",  # Client-side checkout uses client_secret
                message="Payment intent created successfully",
                raw_response={
                    "client_secret": intent.client_secret,
                    "payment_intent_id": intent.id,
                    "customer_id": customer.id,
                    "status": intent.status,
                },
            )
            
        except stripe.error.IdempotencyError as e:
            # Same idempotency key used with different parameters
            logger.warning(f"Idempotency error for {tx_ref}: {str(e)}")
            return PaymentResult(
                success=False,
                message="A payment with this reference already exists with different parameters",
                error_code="idempotency_error",
                raw_response={"error": str(e)},
            )
            
        except stripe.error.CardError as e:
            logger.error(f"Card error for {tx_ref}: {str(e)}")
            return PaymentResult(
                success=False,
                message=e.user_message or "Card error occurred",
                error_code=e.code,
                raw_response={"error": str(e)},
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error for {tx_ref}: {str(e)}")
            return PaymentResult(
                success=False,
                message="Payment initialization failed",
                error_code="stripe_error",
                raw_response={"error": str(e)},
            )
    
    def create_checkout_session(
        self,
        amount: Decimal,
        currency: str,
        email: str,
        tx_ref: str,
        success_url: str,
        cancel_url: str,
        line_items: list = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create a Stripe Checkout Session for hosted checkout.
        
        Use this for a fully hosted checkout experience.
        
        Args:
            amount: Total amount
            currency: Currency code
            email: Customer email
            tx_ref: Transaction reference
            success_url: Redirect URL on success (include {CHECKOUT_SESSION_ID})
            cancel_url: Redirect URL on cancel
            line_items: List of line items (optional, creates single item if not provided)
            description: Payment description
            metadata: Additional metadata
            idempotency_key: Idempotency key
            
        Returns:
            PaymentResult with checkout URL
        """
        try:
            idem_key = idempotency_key or f"cs_{tx_ref}"
            
            # Build line items
            if line_items:
                stripe_line_items = [
                    {
                        "price_data": {
                            "currency": currency.lower(),
                            "unit_amount": int(item["unit_price"] * 100),
                            "product_data": {
                                "name": item["name"],
                                "description": item.get("description", ""),
                            },
                        },
                        "quantity": item["quantity"],
                    }
                    for item in line_items
                ]
            else:
                stripe_line_items = [
                    {
                        "price_data": {
                            "currency": currency.lower(),
                            "unit_amount": int(amount * 100),
                            "product_data": {
                                "name": description or f"Order {tx_ref}",
                            },
                        },
                        "quantity": 1,
                    }
                ]
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=stripe_line_items,
                mode="payment",
                customer_email=email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "tx_ref": tx_ref,
                    **(metadata or {}),
                },
                idempotency_key=idem_key,
            )
            
            logger.info(f"Created Stripe Checkout Session: {session.id} for {tx_ref}")
            
            return PaymentResult(
                success=True,
                provider_transaction_id=session.id,
                checkout_url=session.url,
                message="Checkout session created",
                raw_response={
                    "session_id": session.id,
                    "url": session.url,
                    "status": session.status,
                },
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout error for {tx_ref}: {str(e)}")
            return PaymentResult(
                success=False,
                message="Failed to create checkout session",
                error_code="checkout_error",
                raw_response={"error": str(e)},
            )
    
    def verify_payment(self, tx_ref: str) -> PaymentVerificationResult:
        """
        Verify a payment by transaction reference.
        
        Looks up the PaymentIntent or Checkout Session by metadata.
        
        Args:
            tx_ref: Transaction reference
            
        Returns:
            PaymentVerificationResult
        """
        try:
            # Try to find by PaymentIntent ID first
            if tx_ref.startswith("pi_"):
                intent = stripe.PaymentIntent.retrieve(tx_ref)
                return self._verify_payment_intent(intent)
            
            # Try to find by Checkout Session ID
            if tx_ref.startswith("cs_"):
                session = stripe.checkout.Session.retrieve(tx_ref)
                if session.payment_intent:
                    intent = stripe.PaymentIntent.retrieve(session.payment_intent)
                    return self._verify_payment_intent(intent)
            
            # Search by metadata
            intents = stripe.PaymentIntent.search(
                query=f"metadata['tx_ref']:'{tx_ref}'",
                limit=1,
            )
            
            if intents.data:
                return self._verify_payment_intent(intents.data[0])
            
            return PaymentVerificationResult(
                verified=False,
                status="not_found",
                message="Payment not found",
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Verification error for {tx_ref}: {str(e)}")
            return PaymentVerificationResult(
                verified=False,
                status="error",
                message=str(e),
            )
    
    def _verify_payment_intent(self, intent: stripe.PaymentIntent) -> PaymentVerificationResult:
        """Verify a PaymentIntent object."""
        amount = Decimal(intent.amount) / Decimal("100")
        
        # Calculate Stripe fee (approximate: 2.9% + $0.30 for US)
        fee = (amount * Decimal("0.029") + Decimal("0.30")).quantize(Decimal("0.01"))
        
        verified = intent.status == "succeeded"
        
        return PaymentVerificationResult(
            verified=verified,
            status=intent.status,
            amount=amount,
            currency=intent.currency.upper(),
            provider_fee=fee,
            message="Payment verified" if verified else f"Payment status: {intent.status}",
            raw_response={
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": str(amount),
                "customer": intent.customer,
            },
        )
    
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "",
        idempotency_key: Optional[str] = None,
    ) -> PaymentResult:
        """
        Process a refund for a payment.
        
        Args:
            payment_intent_id: Stripe PaymentIntent ID
            amount: Amount to refund (None = full refund)
            reason: Refund reason
            idempotency_key: Unique key for idempotency
            
        Returns:
            PaymentResult with refund details
        """
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            if reason:
                # Stripe accepts: duplicate, fraudulent, requested_by_customer
                if reason.lower() in ["duplicate", "fraudulent", "requested_by_customer"]:
                    refund_params["reason"] = reason.lower()
            
            idem_key = idempotency_key or f"rf_{payment_intent_id}_{amount or 'full'}"
            
            refund = stripe.Refund.create(
                **refund_params,
                idempotency_key=idem_key,
            )
            
            logger.info(f"Created refund {refund.id} for {payment_intent_id}")
            
            return PaymentResult(
                success=refund.status in ["succeeded", "pending"],
                provider_transaction_id=refund.id,
                message=f"Refund {refund.status}",
                raw_response={
                    "refund_id": refund.id,
                    "status": refund.status,
                    "amount": str(Decimal(refund.amount) / 100),
                },
            )
            
        except stripe.error.StripeError as e:
            logger.error(f"Refund error for {payment_intent_id}: {str(e)}")
            return PaymentResult(
                success=False,
                message="Refund failed",
                error_code="refund_error",
                raw_response={"error": str(e)},
            )
    
    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify and parse a Stripe webhook event.
        
        Args:
            payload: Raw webhook payload bytes
            signature: Stripe-Signature header
            
        Returns:
            Parsed event dict
            
        Raises:
            ValueError: If signature is invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return event
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")
    
    def _get_or_create_customer(
        self,
        email: str,
        name: str = "",
        phone: str = "",
    ) -> stripe.Customer:
        """Get or create a Stripe customer."""
        # Search for existing customer
        customers = stripe.Customer.list(email=email, limit=1)
        
        if customers.data:
            return customers.data[0]
        
        # Create new customer
        return stripe.Customer.create(
            email=email,
            name=name,
            phone=phone,
        )
    
    def create_payment_method_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """
        Create a session for customer to manage payment methods.
        
        Args:
            customer_id: Stripe customer ID
            return_url: Return URL after management
            
        Returns:
            URL for customer portal
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url


# ============================================================================
# Idempotency Key Manager
# ============================================================================

class IdempotencyKeyManager:
    """
    Manages idempotency keys for payment operations.
    
    Ensures that retry operations don't create duplicate charges.
    """
    
    @staticmethod
    def generate_key(operation: str, order_id: str, attempt: int = 0) -> str:
        """
        Generate an idempotency key for an operation.
        
        Args:
            operation: Operation type (e.g., 'payment', 'refund')
            order_id: Order identifier
            attempt: Attempt number (for tracking retries)
            
        Returns:
            Unique idempotency key
        """
        import hashlib
        
        key_data = f"{operation}:{order_id}:{attempt}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    @staticmethod
    def get_payment_key(order_id: str) -> str:
        """Get idempotency key for a payment operation."""
        return IdempotencyKeyManager.generate_key("payment", order_id)
    
    @staticmethod
    def get_refund_key(order_id: str, amount: Decimal = None) -> str:
        """Get idempotency key for a refund operation."""
        suffix = f"_{amount}" if amount else "_full"
        return IdempotencyKeyManager.generate_key("refund", order_id + suffix)
