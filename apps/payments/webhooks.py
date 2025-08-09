"""
Payment webhook views.

This module handles webhook notifications from payment providers
to update transaction status in real-time.
"""

import logging
from typing import Dict, Any

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.swagger_docs import SwaggerTags
from .models import PaymentProvider, Transaction
from .services.factory import get_payment_service_from_provider

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ChapaWebhookView(View):
    """
    Chapa webhook handler.
    
    Processes payment notifications from Chapa to update transaction status.
    """
    
    def post(self, request):
        """Handle Chapa webhook POST request."""
        try:
            # Get webhook data
            webhook_data = request.body
            signature = request.headers.get("X-Chapa-Signature", "")
            
            # Parse JSON data
            import json
            try:
                data = json.loads(webhook_data)
            except json.JSONDecodeError:
                logger.error("Invalid JSON in Chapa webhook")
                return HttpResponse("Invalid JSON", status=400)
            
            # Get Chapa provider
            try:
                provider = PaymentProvider.objects.get(
                    provider_type=PaymentProvider.ProviderType.CHAPA,
                    is_active=True
                )
            except PaymentProvider.DoesNotExist:
                logger.error("Chapa provider not found or inactive")
                return HttpResponse("Provider not found", status=404)
            
            # Process webhook with Chapa service
            payment_service = get_payment_service_from_provider(provider)
            result = payment_service.process_webhook(data, signature)
            
            if not result.get("valid"):
                logger.error(f"Invalid Chapa webhook: {result.get('error')}")
                return HttpResponse("Invalid webhook", status=400)
            
            # Extract transaction reference
            tx_ref = result.get("tx_ref")
            if not tx_ref:
                logger.error("Missing tx_ref in Chapa webhook")
                return HttpResponse("Missing transaction reference", status=400)
            
            # Find and update transaction
            try:
                transaction = Transaction.objects.get(id=tx_ref)
            except Transaction.DoesNotExist:
                logger.error(f"Transaction not found: {tx_ref}")
                return HttpResponse("Transaction not found", status=404)
            
            # Update transaction based on webhook status
            webhook_status = result.get("status", "").lower()
            
            if webhook_status == "success" and result.get("verified"):
                transaction.mark_as_succeeded()
                transaction.webhook_data = result
                transaction.save()
                logger.info(f"Transaction {tx_ref} marked as succeeded via webhook")
            
            elif webhook_status in ["failed", "cancelled"]:
                error_message = f"Payment {webhook_status} - webhook notification"
                transaction.mark_as_failed(error_message)
                transaction.webhook_data = result
                transaction.save()
                logger.info(f"Transaction {tx_ref} marked as {webhook_status} via webhook")
            
            else:
                # Update webhook data but don't change status for other statuses
                transaction.webhook_data = result
                transaction.save()
                logger.info(f"Updated webhook data for transaction {tx_ref}, status: {webhook_status}")
            
            return HttpResponse("OK", status=200)
        
        except Exception as e:
            logger.error(f"Error processing Chapa webhook: {str(e)}")
            return HttpResponse("Internal Server Error", status=500)


@swagger_auto_schema(
    method="post",
    tags=[SwaggerTags.PAYMENT_PROVIDERS],
    operation_summary="Chapa Webhook API",
    operation_description="""
    Handle Chapa payment webhooks with JSON responses.
    
    ### Webhook Events:
    - Payment successful
    - Payment failed
    - Payment pending
    - Refund processed
    
    ### Security:
    - Webhook signature verification
    - Payload validation
    - Secure transaction processing
    
    ### Response Format:
    - JSON responses for all scenarios
    - Detailed error messages
    - Transaction status updates
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "tx_ref": openapi.Schema(type=openapi.TYPE_STRING, description="Transaction reference"),
            "status": openapi.Schema(type=openapi.TYPE_STRING, description="Payment status"),
            "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Payment amount"),
            "currency": openapi.Schema(type=openapi.TYPE_STRING, description="Payment currency"),
        },
    ),
    responses={
        200: openapi.Response(
            "Webhook processed successfully",
            examples={
                "application/json": {
                    "success": True,
                    "message": "Webhook processed successfully",
                    "transaction_status": "completed"
                }
            },
        ),
        400: openapi.Response(
            "Invalid webhook data",
            examples={
                "application/json": {
                    "error": "Invalid webhook",
                    "details": "Missing transaction reference"
                }
            },
        ),
        404: openapi.Response(
            "Provider not found",
            examples={
                "application/json": {
                    "error": "Chapa provider not found"
                }
            },
        ),
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def chapa_webhook_api(request):
    """
    API endpoint for Chapa webhooks.
    
    Alternative webhook endpoint that returns JSON responses.
    """
    try:
        webhook_data = request.data
        signature = request.headers.get("X-Chapa-Signature", "")
        
        # Get Chapa provider
        try:
            provider = PaymentProvider.objects.get(
                provider_type=PaymentProvider.ProviderType.CHAPA,
                is_active=True
            )
        except PaymentProvider.DoesNotExist:
            return Response(
                {"error": "Chapa provider not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process webhook
        payment_service = get_payment_service_from_provider(provider)
        result = payment_service.process_webhook(webhook_data, signature)
        
        if not result.get("valid"):
            return Response(
                {"error": "Invalid webhook", "details": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and update transaction
        tx_ref = result.get("tx_ref")
        if not tx_ref:
            return Response(
                {"error": "Missing transaction reference"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction = Transaction.objects.get(id=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update transaction
        webhook_status = result.get("status", "").lower()
        
        if webhook_status == "success" and result.get("verified"):
            transaction.mark_as_succeeded()
            transaction.webhook_data = result
            transaction.save()
        elif webhook_status in ["failed", "cancelled"]:
            error_message = f"Payment {webhook_status} - webhook notification"
            transaction.mark_as_failed(error_message)
            transaction.webhook_data = result
            transaction.save()
        else:
            transaction.webhook_data = result
            transaction.save()
        
        return Response({
            "status": "success",
            "message": "Webhook processed successfully",
            "transaction_id": str(transaction.id),
            "transaction_status": transaction.status,
        })
    
    except Exception as e:
        logger.error(f"Error processing Chapa webhook API: {str(e)}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_payment_callback(request):
    """
    Handle payment verification callbacks.
    
    This endpoint can be used as a callback URL for payment verification.
    """
    try:
        # Extract parameters from request
        tx_ref = request.data.get("trx_ref") or request.GET.get("trx_ref")
        ref_id = request.data.get("ref_id") or request.GET.get("ref_id")
        callback_status = request.data.get("status") or request.GET.get("status")
        
        if not tx_ref:
            return Response(
                {"error": "Missing transaction reference"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find transaction
        try:
            transaction = Transaction.objects.get(id=tx_ref)
        except Transaction.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify payment with provider
        payment_service = get_payment_service_from_provider(transaction.provider)
        verification_result = payment_service.verify_payment(tx_ref)
        
        # Update transaction based on verification result
        if verification_result.verified:
            transaction.mark_as_succeeded()
            transaction.provider_fee = verification_result.provider_fee
            transaction.metadata.update({
                "verification_result": verification_result.raw_response,
                "callback_ref_id": ref_id,
                "callback_status": callback_status,
            })
            transaction.save()
        else:
            transaction.mark_as_failed(verification_result.message)
            transaction.metadata.update({
                "verification_result": verification_result.raw_response,
                "callback_ref_id": ref_id,
                "callback_status": callback_status,
            })
            transaction.save()
        
        return Response({
            "status": "success",
            "message": "Payment verification completed",
            "transaction_id": str(transaction.id),
            "transaction_status": transaction.status,
            "verified": verification_result.verified,
        })
    
    except Exception as e:
        logger.error(f"Error in payment verification callback: {str(e)}")
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
