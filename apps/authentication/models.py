"""
User authentication models.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    """
    Custom user model with additional fields.
    """

    USER_ROLES = [
        ("customer", "Customer"),
        ("staff", "Staff"),
        ("admin", "Admin"),
        ("super_admin", "Super Admin"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        unique=True, help_text="User's email address (used for login)"
    )
    first_name = models.CharField(
        max_length=150, blank=True, help_text="User's first name"
    )
    last_name = models.CharField(
        max_length=150, blank=True, help_text="User's last name"
    )
    phone_number = models.CharField(
        max_length=15, blank=True, help_text="User's phone number"
    )
    is_verified = models.BooleanField(
        default=False, help_text="Whether user has verified their email"
    )
    date_of_birth = models.DateField(
        null=True, blank=True, help_text="User's date of birth"
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, help_text="User's profile picture"
    )
    
    # Enhanced user fields
    role = models.CharField(
        max_length=20, choices=USER_ROLES, default="customer", help_text="User role"
    )
    is_email_verified = models.BooleanField(
        default=False, help_text="Whether user email is verified"
    )
    email_verification_sent_at = models.DateTimeField(
        null=True, blank=True, help_text="When email verification was last sent"
    )
    
    # Account security
    failed_login_attempts = models.PositiveIntegerField(
        default=0, help_text="Number of consecutive failed login attempts"
    )
    account_locked_until = models.DateTimeField(
        null=True, blank=True, help_text="Account locked until this time"
    )
    last_password_change = models.DateTimeField(
        null=True, blank=True, help_text="When password was last changed"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["is_email_verified"]),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_profile_complete(self):
        """Check if user profile is complete."""
        basic_complete = bool(self.first_name and self.last_name and self.phone_number)
        if hasattr(self, 'profile'):
            return basic_complete and self.profile.completion_percentage >= 70
        return basic_complete

    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if not self.account_locked_until:
            return False
        from django.utils import timezone
        return timezone.now() < self.account_locked_until

    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary."""
        from django.utils import timezone
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
            
        self.save(update_fields=["failed_login_attempts", "account_locked_until"])

    def reset_failed_login_attempts(self):
        """Reset failed login attempts on successful login."""
        if self.failed_login_attempts > 0 or self.account_locked_until:
            self.failed_login_attempts = 0
            self.account_locked_until = None
            self.save(update_fields=["failed_login_attempts", "account_locked_until"])

    def verify_email(self):
        """Mark email as verified."""
        self.is_email_verified = True
        self.is_verified = True  # Keep backward compatibility
        self.save(update_fields=["is_email_verified", "is_verified"])

    def has_role(self, role):
        """Check if user has specific role or higher."""
        role_hierarchy = {
            "customer": 1,
            "staff": 2,
            "admin": 3,
            "super_admin": 4,
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(role, 0)
        return user_level >= required_level


# Import related models
from .models.profile import UserProfile, UserAddress
from .models.verification import EmailVerificationToken, PasswordResetToken, UserActivity


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)
