"""
Enhanced authentication views with email verification and password reset.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.capture_decorator import capture_for_swagger
from apps.core.swagger_docs import SwaggerTags, get_example_or_fallback
from apps.core.throttling.decorators import registration_ratelimit

from ..serializers import (
    EmailVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendVerificationSerializer,
)
from ..utils import (
    can_resend_verification,
    create_email_verification_token,
    create_password_reset_token,
    log_user_activity,
    reset_password_with_token,
    send_password_reset_email,
    send_verification_email,
    verify_email_with_token,
)

User = get_user_model()


class EmailVerificationView(APIView):
    """
    ## Email Verification

    Handle email verification for new user accounts.

    ### 📧 Verification Process
    - User receives verification email after registration
    - Click verification link or submit token via API
    - Email marked as verified upon successful verification
    - Account fully activated

    ### 🔐 Security Features
    - Tokens expire after 24 hours
    - One-time use tokens
    - Secure token generation
    - Activity logging
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Verify Email Address",
        operation_description="""
        Verify user email address using verification token.
        
        ### Process:
        1. User receives verification email after registration
        2. Token extracted from verification link or entered manually
        3. Submit token to this endpoint
        4. Email verified and account activated
        
        ### Token Security:
        - Tokens expire in 24 hours
        - Single-use tokens (become invalid after verification)
        - Cryptographically secure generation
        """,
        request_body=EmailVerificationSerializer,
        responses={
            200: openapi.Response(
                "Email verified successfully",
                examples={
                    "application/json": {
                        "message": "Email verified successfully",
                        "user": {
                            "id": "user-uuid",
                            "email": "user@example.com",
                            "is_email_verified": True,
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Invalid or expired token",
                examples={"application/json": {"token": ["Invalid or expired token."]}},
            ),
        },
    )
    @capture_for_swagger("email_verification")
    def post(self, request):
        """Verify email address with token."""
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]
            success, message = verify_email_with_token(token)

            if success:
                # Get user from token for response
                from ..models import EmailVerificationToken

                token_obj = EmailVerificationToken.objects.get(token=token)
                user = token_obj.user

                return Response(
                    {
                        "message": message,
                        "user": {
                            "id": str(user.id),
                            "email": user.email,
                            "is_email_verified": user.is_email_verified,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """Verify email address via GET request (for email links)."""
        token = request.GET.get('token')
        if not token:
            return Response(
                {"error": "Token parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        success, message = verify_email_with_token(token)

        if success:
            # Return a simple HTML response for email link clicks
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email Verified - Bazary</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #28a745; }}
                    .container {{ max-width: 500px; margin: 0 auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✓ Email Verified Successfully!</h1>
                    <p>{message}</p>
                    <p>Your account is now active. You can close this window.</p>
                </div>
            </body>
            </html>
            """
            from django.http import HttpResponse
            return HttpResponse(html_content, content_type='text/html')
        else:
            # Return error HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Verification Failed - Bazary</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #dc3545; }}
                    .container {{ max-width: 500px; margin: 0 auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">✗ Verification Failed</h1>
                    <p>{message}</p>
                    <p>Please request a new verification email if needed.</p>
                </div>
            </body>
            </html>
            """
            from django.http import HttpResponse
            return HttpResponse(html_content, content_type='text/html', status=400)


class ResendVerificationView(APIView):
    """
    ## Resend Email Verification

    Resend email verification link for unverified accounts.

    ### 📧 Resend Process
    - Rate limited to prevent spam
    - Only for unverified emails
    - Invalidates previous tokens
    - Sends new verification email

    ### 🔐 Security Features
    - Rate limiting (5 minutes between requests)
    - Email existence validation
    - Activity logging
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Resend Email Verification",
        operation_description="""
        Resend email verification link for unverified user accounts.
        
        ### Requirements:
        - Email must be registered but not verified
        - Must wait 5 minutes between resend requests
        - User account must be active
        
        ### Process:
        1. Validate email exists and is unverified
        2. Check rate limiting (5 minute cooldown)
        3. Generate new verification token
        4. Send verification email
        5. Log activity for security
        """,
        request_body=ResendVerificationSerializer,
        responses={
            200: openapi.Response(
                "Verification email sent",
                examples={
                    "application/json": {
                        "message": "Verification email sent successfully",
                        "email": "user@example.com",
                    }
                },
            ),
            400: openapi.Response(
                "Cannot resend verification",
                examples={"application/json": {"error": "Email is already verified"}},
            ),
            429: openapi.Response(
                "Rate limited",
                examples={
                    "application/json": {
                        "error": "Please wait 4 minutes before requesting again"
                    }
                },
            ),
        },
    )
    @capture_for_swagger("resend_verification")
    @registration_ratelimit(rate="3/h")
    def post(self, request):
        """Resend email verification."""
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            # Check if can resend
            can_resend, message = can_resend_verification(user)
            if not can_resend:
                return Response(
                    {"error": message}, status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Create and send verification token
            token = create_email_verification_token(user)
            email_sent = send_verification_email(user, token)

            if email_sent:
                log_user_activity(
                    user=user,
                    action="email_verification",
                    description="Verification email resent",
                    request=request,
                )

                return Response(
                    {
                        "message": "Verification email sent successfully",
                        "email": user.email,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Failed to send verification email"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    ## Password Reset Request

    Request password reset link via email.

    ### 🔒 Reset Process
    - Email validation (no indication if email exists)
    - Time-limited reset tokens (1 hour)
    - Secure token generation
    - IP address and user agent logging

    ### 🔐 Security Features
    - Rate limiting to prevent abuse
    - No email enumeration (same response for valid/invalid emails)
    - Secure token generation
    - Activity logging with IP tracking
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Request Password Reset",
        operation_description="""
        Request password reset link to be sent via email.
        
        ### Security Design:
        - No indication whether email exists (prevents email enumeration)
        - Same response for valid and invalid emails
        - Rate limited to prevent abuse
        
        ### Process:
        1. User submits email address
        2. If email exists, generate secure reset token
        3. Send password reset email with token
        4. Log security activity with IP address
        5. Return success response (regardless of email validity)
        
        ### Token Security:
        - Tokens expire in 1 hour
        - Single-use tokens
        - IP address and user agent logged
        """,
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                "Reset email sent (or would be sent)",
                examples={
                    "application/json": {
                        "message": "If an account with this email exists, a password reset link has been sent.",
                        "email": "user@example.com",
                    }
                },
            ),
        },
    )
    @capture_for_swagger("password_reset_request")
    @registration_ratelimit(rate="3/h")
    def post(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # Always return same response to prevent email enumeration
            response_data = {
                "message": "If an account with this email exists, a password reset link has been sent.",
                "email": email,
            }

            try:
                user = User.objects.get(email=email, is_active=True)

                # Create and send reset token
                token = create_password_reset_token(user, request)
                email_sent = send_password_reset_email(user, token)

                if email_sent:
                    log_user_activity(
                        user=user,
                        action="password_reset",
                        description="Password reset requested",
                        request=request,
                    )

            except User.DoesNotExist:
                # Log potential security issue but don't reveal it
                pass

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    ## Password Reset Confirmation

    Confirm password reset using token and set new password.

    ### 🔒 Confirmation Process
    - Token validation and expiry check
    - Password strength validation
    - Account security reset
    - Activity logging

    ### 🔐 Security Features
    - One-time use tokens
    - Strong password requirements
    - Failed login attempts reset
    - Comprehensive activity logging
    """

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=[SwaggerTags.AUTHENTICATION],
        operation_summary="Confirm Password Reset",
        operation_description="""
        Complete password reset process using token and new password.
        
        ### Process:
        1. Validate reset token (must be valid and not expired)
        2. Validate new password meets strength requirements
        3. Update user password with secure hashing
        4. Clear any failed login attempts
        5. Mark token as used (prevents reuse)
        6. Log security activity
        
        ### Security Benefits:
        - Token becomes invalid after use
        - Password strength validation enforced
        - Failed login attempts cleared
        - Last password change timestamp updated
        - Complete audit trail logged
        """,
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: openapi.Response(
                "Password reset successfully",
                examples={
                    "application/json": {
                        "message": "Password reset successfully",
                        "user": {
                            "id": "user-uuid",
                            "email": "user@example.com",
                            "last_password_change": "2025-01-01T12:00:00Z",
                        },
                    }
                },
            ),
            400: openapi.Response(
                "Invalid token or password validation error",
                examples={
                    "application/json": {
                        "token": ["Invalid or expired token."],
                        "new_password": ["Password too weak."],
                    }
                },
            ),
        },
    )
    @capture_for_swagger("password_reset_confirm")
    def post(self, request):
        """Confirm password reset with token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            success, message = reset_password_with_token(token, new_password)

            if success:
                # Get user from token for response
                from ..models import PasswordResetToken

                token_obj = PasswordResetToken.objects.get(token=token)
                user = token_obj.user

                return Response(
                    {
                        "message": message,
                        "user": {
                            "id": str(user.id),
                            "email": user.email,
                            "last_password_change": (
                                user.last_password_change.isoformat()
                                if user.last_password_change
                                else None
                            ),
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
