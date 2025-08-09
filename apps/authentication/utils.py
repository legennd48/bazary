"""
Utility functions for user management features.
"""

import secrets
import string
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import EmailVerificationToken, PasswordResetToken, UserActivity

User = get_user_model()


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_client_ip(request) -> Optional[str]:
    """Get client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_user_agent(request) -> str:
    """Get user agent from request."""
    return request.META.get("HTTP_USER_AGENT", "")


def log_user_activity(
    user: User, action: str, description: str = "", request=None, metadata: dict = None
) -> UserActivity:
    """Log user activity for audit purposes."""
    activity_data = {
        "user": user,
        "action": action,
        "description": description,
        "metadata": metadata or {},
    }

    if request:
        activity_data.update(
            {
                "ip_address": get_client_ip(request),
                "user_agent": get_user_agent(request),
            }
        )

    return UserActivity.objects.create(**activity_data)


def create_email_verification_token(user: User) -> EmailVerificationToken:
    """Create email verification token for user."""
    # Invalidate existing tokens
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)

    # Create new token
    token = EmailVerificationToken.objects.create(
        user=user, token=generate_secure_token(64)
    )

    # Update user's verification sent timestamp
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=["email_verification_sent_at"])

    return token


def create_password_reset_token(user: User, request=None) -> PasswordResetToken:
    """Create password reset token for user."""
    # Invalidate existing tokens
    PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)

    # Create new token
    token_data = {"user": user, "token": generate_secure_token(64)}

    if request:
        token_data.update(
            {
                "ip_address": get_client_ip(request),
                "user_agent": get_user_agent(request),
            }
        )

    return PasswordResetToken.objects.create(**token_data)


def send_verification_email(user: User, token: EmailVerificationToken) -> bool:
    """Send email verification email."""
    try:
        # Use the Django API endpoint directly for verification
        verification_url = f"http://localhost:8001/api/v1/auth/verify-email/?token={token.token}"

        context = {
            "user": user,
            "verification_url": verification_url,
            "site_name": getattr(settings, "SITE_NAME", "Bazary"),
            "token_expires_hours": 24,
            "token": token.token,  # Add token separately for manual entry
        }

        html_message = render_to_string("emails/verify_email.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Verify your email for {context["site_name"]}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        return True
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Failed to send verification email: {e}")
        return False


def send_password_reset_email(user: User, token: PasswordResetToken) -> bool:
    """Send password reset email."""
    try:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"

        context = {
            "user": user,
            "reset_url": reset_url,
            "site_name": getattr(settings, "SITE_NAME", "Bazary"),
            "token_expires_hours": 1,
            "ip_address": token.ip_address,
        }

        html_message = render_to_string("emails/password_reset.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f'Password reset for {context["site_name"]}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
        )

        return True
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Failed to send password reset email: {e}")
        return False


def verify_email_with_token(token_value: str) -> tuple[bool, str]:
    """Verify email using token."""
    try:
        token = EmailVerificationToken.objects.get(token=token_value)

        if not token.is_valid:
            return False, "Token is invalid or expired"

        # Mark token as used
        token.use_token()

        # Verify user email
        user = token.user
        user.verify_email()

        # Log activity
        log_user_activity(
            user=user,
            action="email_verification",
            description="Email verified successfully",
        )

        return True, "Email verified successfully"

    except EmailVerificationToken.DoesNotExist:
        return False, "Invalid token"


def reset_password_with_token(token_value: str, new_password: str) -> tuple[bool, str]:
    """Reset password using token."""
    try:
        token = PasswordResetToken.objects.get(token=token_value)

        if not token.is_valid:
            return False, "Token is invalid or expired"

        # Mark token as used
        token.use_token()

        # Reset password
        user = token.user
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.reset_failed_login_attempts()  # Clear any login attempts
        user.save()

        # Log activity
        log_user_activity(
            user=user,
            action="password_reset",
            description="Password reset successfully",
            metadata={"ip_address": token.ip_address},
        )

        return True, "Password reset successfully"

    except PasswordResetToken.DoesNotExist:
        return False, "Invalid token"


def can_resend_verification(user: User) -> tuple[bool, str]:
    """Check if user can resend verification email."""
    if user.is_email_verified:
        return False, "Email is already verified"

    if user.email_verification_sent_at:
        # Allow resend after 5 minutes
        from datetime import timedelta

        time_diff = timezone.now() - user.email_verification_sent_at
        if time_diff < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - time_diff
            return (
                False,
                f"Please wait {remaining.seconds // 60} minutes before requesting again",
            )

    return True, "Can resend verification"


def bulk_user_action(
    user_ids: list, action: str, admin_user: User, reason: str = ""
) -> dict:
    """Perform bulk action on users."""
    users = User.objects.filter(id__in=user_ids)
    success_count = 0
    errors = []

    for user in users:
        try:
            if action == "activate":
                user.is_active = True
                user.save()
                log_user_activity(
                    user=user,
                    action="account_activation",
                    description=f"Account activated by {admin_user.email}. Reason: {reason}",
                )
            elif action == "deactivate":
                user.is_active = False
                user.save()
                log_user_activity(
                    user=user,
                    action="account_deactivation",
                    description=f"Account deactivated by {admin_user.email}. Reason: {reason}",
                )
            elif action == "verify_email":
                user.verify_email()
                log_user_activity(
                    user=user,
                    action="email_verification",
                    description=f"Email verified by admin {admin_user.email}. Reason: {reason}",
                )
            elif action == "reset_failed_attempts":
                user.reset_failed_login_attempts()
                log_user_activity(
                    user=user,
                    action="login",
                    description=f"Failed login attempts reset by {admin_user.email}. Reason: {reason}",
                )
            elif action == "send_verification":
                if not user.is_email_verified:
                    token = create_email_verification_token(user)
                    send_verification_email(user, token)
                    log_user_activity(
                        user=user,
                        action="email_verification",
                        description=f"Verification email sent by admin {admin_user.email}",
                    )

            success_count += 1

        except Exception as e:
            errors.append(f"Error with user {user.email}: {str(e)}")

    return {
        "success_count": success_count,
        "total_count": len(user_ids),
        "errors": errors,
    }
