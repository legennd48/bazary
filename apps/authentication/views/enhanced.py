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
        tags=[SwaggerTags.EMAIL_VERIFICATION],
        operation_summary="📧 Verify Email Address",
        operation_description="""
        ## 📧 Complete Email Verification Process
        
        Verify user email address using secure verification tokens.
        
        ### 📋 Verification Process:
        1. **Token Reception**: User receives token via registration or resend email
        2. **Token Submission**: Submit token via POST request or GET link click
        3. **Validation**: System validates token authenticity and expiration
        4. **Account Activation**: Email marked as verified, account fully activated
        
        ### 🔗 Verification Methods:
        
        #### Method 1: API Submission (POST)
        ```bash
        curl -X POST /api/v1/auth/verify-email/ \\
          -H "Content-Type: application/json" \\
          -d '{"token": "YOUR_64_CHAR_TOKEN"}'
        ```
        
        #### Method 2: Email Link Click (GET)
        ```
        Click the verification link in your email, or visit:
        http://localhost:8001/api/v1/auth/verify-email/?token=YOUR_TOKEN
        ```
        
        ### 🔐 Token Security Features:
        - **64-Character Length**: Cryptographically secure random generation
        - **24-Hour Expiration**: Tokens automatically expire for security
        - **Single-Use Only**: Tokens become invalid after successful verification
        - **User-Specific**: Each token is tied to a specific user account
        
        ### ✅ Success Outcomes:
        - Email address marked as verified in user profile
        - Account gains full access to authenticated features
        - User can login without additional verification steps
        - Verification token marked as used (prevents reuse)
        
        ### 🔄 If Token Issues:
        - **Expired**: Request new token via `/resend-verification/` endpoint
        - **Invalid**: Check token copied correctly from email
        - **Already Used**: Account may already be verified
        - **Not Found**: Token may be from different environment
        
        ### 🧪 Testing the Endpoint:
        ```bash
        # Test with POST request
        curl -X POST "http://localhost:8001/api/v1/auth/verify-email/" \\
          -H "Content-Type: application/json" \\
          -d '{"token": "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz5678ab9012cd3456"}'
        
        # Test with GET request (email link simulation)
        curl "http://localhost:8001/api/v1/auth/verify-email/?token=YOUR_TOKEN"
        ```
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

    @swagger_auto_schema(
        tags=[SwaggerTags.EMAIL_VERIFICATION],
        operation_summary="🔗 Verify Email via URL",
        operation_description="""
        Verify email address via GET request (for email links).
        
        ### 📧 Email Link Verification:
        This endpoint is designed to be called directly from email verification links.
        Users click the link in their email and are automatically verified.
        
        ### 🔗 URL Format:
        ```
        GET /api/v1/auth/verify-email/?token=YOUR_64_CHAR_TOKEN
        ```
        
        ### 🔄 Process Flow:
        1. User receives verification email with link
        2. User clicks link in email client
        3. Browser opens this endpoint with token parameter
        4. Server verifies token and updates account
        5. User redirected to success page
        
        ### ✅ Success Response:
        - HTTP 200 with verification confirmation
        - Account automatically verified
        - User can proceed to login
        """,
        manual_parameters=[
            openapi.Parameter(
                "token",
                openapi.IN_QUERY,
                description="64-character email verification token from email",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ],
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
                examples={"application/json": {"error": "Invalid or expired token"}},
            ),
        },
    )
    def get(self, request):
        """Verify email address via GET request (for email links)."""
        token = request.GET.get("token")
        if not token:
            return Response(
                {"error": "Token parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
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

            return HttpResponse(html_content, content_type="text/html")
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

            return HttpResponse(html_content, content_type="text/html", status=400)


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
        tags=[SwaggerTags.EMAIL_VERIFICATION],
        operation_summary="🔄 Resend Email Verification",
        operation_description="""
        ## 📧 Resend Email Verification Token
        
        Request a new email verification token for unverified accounts.
        
        ### 📋 Resend Process:
        1. **Account Validation**: Confirms email exists and is unverified
        2. **Rate Limit Check**: Ensures 5-minute cooldown between requests
        3. **Token Generation**: Creates new secure 64-character token
        4. **Email Delivery**: Sends fresh verification email
        5. **Token Invalidation**: Previous tokens become invalid
        
        ### ⏰ Rate Limiting:
        - **Cooldown Period**: 5 minutes between resend requests
        - **Security Measure**: Prevents email spam and abuse
        - **User-Friendly**: Clear messaging about wait time
        - **Automatic Reset**: Cooldown resets after successful verification
        
        ### 🎯 Use Cases:
        - **Email Not Received**: Original verification email missing/delayed
        - **Token Expired**: Previous token exceeded 24-hour limit
        - **Email Issues**: Problems with email delivery or formatting
        - **User Request**: User specifically requests new verification email
        
        ### 📧 Email Content:
        New verification emails include:
        - **Clickable Link**: Direct verification via email click
        - **Manual Token**: 64-character token for API submission
        - **Clear Instructions**: Step-by-step verification guide
        - **Security Notice**: Information about token expiration
        
        ### 🔐 Security Features:
        - **Email Validation**: Must be registered but unverified
        - **Account Status**: Only active accounts can request resend
        - **Token Uniqueness**: Each resend generates unique token
        - **Audit Logging**: Resend requests logged for security
        
        ### 🧪 Testing Examples:
        ```bash
        # Request resend for unverified email
        curl -X POST "http://localhost:8001/api/v1/auth/resend-verification/" \\
          -H "Content-Type: application/json" \\
          -d '{"email": "user@example.com"}'
        
        # Expected success response
        {
          "message": "Verification email sent successfully",
          "email": "user@example.com"
        }
        
        # Test rate limiting (send again within 5 minutes)
        curl -X POST "http://localhost:8001/api/v1/auth/resend-verification/" \\
          -H "Content-Type: application/json" \\
          -d '{"email": "user@example.com"}'
        
        # Expected rate limit response (429)
        {
          "error": "Please wait 4 minutes before requesting again"
        }
        ```
        
        ### ⚠️ Error Scenarios:
        - **Already Verified**: Email address already confirmed
        - **Rate Limited**: Too many requests within 5-minute window
        - **Account Not Found**: Email not registered in system
        - **Inactive Account**: Account deactivated or suspended
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
        tags=[SwaggerTags.PASSWORD_MANAGEMENT],
        operation_summary="🔑 Request Password Reset",
        operation_description="""
        ## 🔐 Request Password Reset Token
        
        Initiate password reset process by requesting a secure reset token via email.
        
        ### 🎯 Reset Request Process:
        1. **Email Validation**: Confirms account exists and is active
        2. **Token Generation**: Creates secure 64-character reset token
        3. **Security Check**: Rate limiting prevents abuse
        4. **Email Dispatch**: Sends password reset instructions
        5. **Token Activation**: Reset token becomes valid for 1 hour
        
        ### 📧 Reset Email Content:
        Password reset emails include:
        - **Secure Reset Link**: Direct password reset via email click
        - **Manual Token**: 64-character token for API-based reset
        - **Step-by-Step Guide**: Clear instructions for password change
        - **Security Warning**: Information about token expiration and security
        - **Contact Support**: Assistance information if needed
        
        ### ⏰ Security & Rate Limiting:
        - **Token Expiration**: 1-hour validity period
        - **Rate Limiting**: 3 requests per hour per IP
        - **Single Use**: Each token can only be used once
        - **No Email Enumeration**: Same response for existing/non-existing emails
        - **Audit Logging**: All reset requests logged with IP and user agent
        
        ### 🔒 Security Features:
        - **Email Ownership**: Must have access to registered email
        - **Token Uniqueness**: Each request generates unique token
        - **Secure Generation**: Cryptographically secure random tokens
        - **No Password Exposure**: Current password never transmitted
        - **Privacy Protection**: No indication if email exists in system
        
        ### 🧪 Testing Examples:
        ```bash
        # Request password reset
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-request/" \\
          -H "Content-Type: application/json" \\
          -d '{"email": "user@example.com"}'
        
        # Expected success response (always same)
        {
          "message": "If an account with this email exists, a password reset link has been sent.",
          "email": "user@example.com"
        }
        
        # Test with non-existent email (security response - identical)
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-request/" \\
          -H "Content-Type: application/json" \\
          -d '{"email": "nonexistent@example.com"}'
        
        # Expected response (same for security)
        {
          "message": "If an account with this email exists, a password reset link has been sent.",
          "email": "nonexistent@example.com"
        }
        
        # Test rate limiting (4th request in same hour)
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-request/" \\
          -H "Content-Type: application/json" \\
          -d '{"email": "user@example.com"}'
        
        # Expected rate limit response (429)
        {
          "error": "Rate limit exceeded. Try again later."
        }
        ```
        
        ### 🎯 Use Cases:
        - **Forgotten Password**: User cannot remember current password
        - **Account Recovery**: Regaining access to locked account
        - **Security Precaution**: Changing password after potential compromise
        - **Mobile Reset**: Easy password change from mobile devices
        
        ### ⚠️ Important Security Notes:
        - **Consistent Response**: Identical response for existing/non-existing emails
        - **Email Required**: Must have access to registered email address
        - **One Token**: Previous reset tokens invalidated upon new request
        - **Time Sensitive**: Complete reset within 1-hour window
        - **IP Tracking**: All requests logged with IP address for security
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
        tags=[SwaggerTags.PASSWORD_MANAGEMENT],
        operation_summary="✅ Confirm Password Reset",
        operation_description="""
        ## 🔐 Complete Password Reset Process
        
        Finalize password reset using the token from email and set a new secure password.
        
        ### 🎯 Confirmation Process:
        1. **Token Validation**: Verifies token is valid and not expired
        2. **Password Strength**: Validates new password meets security requirements
        3. **Account Update**: Securely updates password with proper hashing
        4. **Security Reset**: Clears failed login attempts and updates timestamps
        5. **Token Invalidation**: Marks token as used to prevent reuse
        6. **Activity Logging**: Records password change for security audit
        
        ### 🔒 Password Requirements:
        Password must meet these criteria:
        - **Length**: Minimum 8 characters, recommended 12+
        - **Complexity**: Mix of uppercase, lowercase, numbers, and symbols
        - **Uniqueness**: Cannot be the same as previous password
        - **Common Words**: Avoid dictionary words and common patterns
        - **Personal Info**: Should not contain email, name, or personal details
        
        ### 🛡️ Security Features:
        - **One-Time Use**: Token becomes invalid after successful use
        - **Time Expiration**: Tokens expire after 1 hour for security
        - **Secure Hashing**: Password stored with bcrypt/PBKDF2 hashing
        - **Session Management**: All existing sessions invalidated after reset
        - **Failed Attempts**: Login failure counters reset upon successful reset
        
        ### 📊 Response Information:
        Successful reset provides:
        - **Confirmation Message**: Clear success notification
        - **User Details**: Updated account information
        - **Last Change**: Timestamp of password update
        - **Account Status**: Verification of account state
        
        ### 🧪 Testing Examples:
        ```bash
        # Confirm password reset with valid token
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-confirm/" \\
          -H "Content-Type: application/json" \\
          -d '{
            "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yzabc567def890gh",
            "new_password": "NewSecure123!"
          }'
        
        # Expected success response
        {
          "message": "Password reset successfully",
          "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "last_password_change": "2025-01-01T12:00:00Z"
          }
        }
        
        # Test with expired token
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-confirm/" \\
          -H "Content-Type: application/json" \\
          -d '{
            "token": "expired_token_here",
            "new_password": "NewSecure123!"
          }'
        
        # Expected error response (400)
        {
          "token": ["Invalid or expired token."]
        }
        
        # Test with weak password
        curl -X POST "http://localhost:8001/api/v1/auth/password-reset-confirm/" \\
          -H "Content-Type: application/json" \\
          -d '{
            "token": "valid_token_here",
            "new_password": "123"
          }'
        
        # Expected validation error (400)
        {
          "new_password": [
            "This password is too short. It must contain at least 8 characters.",
            "This password is too common."
          ]
        }
        ```
        
        ### 🎯 Use Cases:
        - **Password Recovery**: Complete forgotten password reset process
        - **Security Response**: Change password after security incident
        - **Account Takeover**: Regain control of compromised account
        - **Proactive Security**: Regular password updates for better security
        
        ### ⚠️ Important Notes:
        - **Token Lifespan**: Must complete reset within 1 hour of request
        - **Single Use**: Each token can only be used once
        - **Session Impact**: All existing login sessions will be invalidated
        - **Security Audit**: Password change events are logged for security
        - **Account Access**: Use new password for all future logins
        
        ### 🔄 Post-Reset Actions:
        After successful password reset:
        1. **Immediate Login**: Use new password to access account
        2. **Session Review**: Check active sessions and revoke if needed
        3. **Security Check**: Review account activity for unauthorized access
        4. **Device Update**: Update password on all saved devices
        5. **Backup Codes**: Generate new backup codes if using 2FA
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
