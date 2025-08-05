"""
User profile models for extended user information.
"""

import uuid

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Extended user profile information.
    """

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("N", "Prefer not to say"),
    ]

    NOTIFICATION_PREFERENCES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push Notifications"),
        ("none", "No Notifications"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    
    # Personal Information
    bio = models.TextField(max_length=500, blank=True, help_text="User biography")
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, blank=True, help_text="User gender"
    )
    website = models.URLField(blank=True, help_text="User's website URL")
    location = models.CharField(
        max_length=100, blank=True, help_text="User's location"
    )
    
    # Preferences
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="User's preferred timezone"
    )
    language = models.CharField(
        max_length=10,
        default="en",
        help_text="User's preferred language"
    )
    notification_preference = models.CharField(
        max_length=10,
        choices=NOTIFICATION_PREFERENCES,
        default="email",
        help_text="Preferred notification method"
    )
    
    # Privacy Settings
    is_profile_public = models.BooleanField(
        default=True, help_text="Whether profile is publicly visible"
    )
    show_email = models.BooleanField(
        default=False, help_text="Whether to show email publicly"
    )
    show_phone = models.BooleanField(
        default=False, help_text="Whether to show phone publicly"
    )
    
    # Marketing and Communication
    marketing_emails = models.BooleanField(
        default=True, help_text="Receive marketing emails"
    )
    product_updates = models.BooleanField(
        default=True, help_text="Receive product update notifications"
    )
    newsletter = models.BooleanField(
        default=False, help_text="Subscribe to newsletter"
    )
    
    # Account Statistics
    login_count = models.PositiveIntegerField(
        default=0, help_text="Total number of logins"
    )
    last_activity = models.DateTimeField(
        null=True, blank=True, help_text="Last activity timestamp"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_profile_public"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def completion_percentage(self):
        """Calculate profile completion percentage."""
        fields_to_check = [
            self.user.first_name,
            self.user.last_name,
            self.user.phone_number,
            self.user.date_of_birth,
            self.bio,
            self.location,
            self.user.avatar,
        ]
        
        completed_fields = sum(1 for field in fields_to_check if field)
        total_fields = len(fields_to_check)
        
        return round((completed_fields / total_fields) * 100, 1)

    def increment_login_count(self):
        """Increment login count."""
        self.login_count += 1
        self.save(update_fields=["login_count"])

    def update_last_activity(self):
        """Update last activity timestamp."""
        from django.utils import timezone
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])


class UserAddress(models.Model):
    """
    User address information for shipping and billing.
    """

    ADDRESS_TYPES = [
        ("shipping", "Shipping Address"),
        ("billing", "Billing Address"),
        ("both", "Shipping & Billing"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    
    # Address Information
    address_type = models.CharField(
        max_length=20, choices=ADDRESS_TYPES, default="shipping"
    )
    is_default = models.BooleanField(default=False)
    
    # Address Fields
    street_address = models.CharField(max_length=255)
    apartment_number = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Contact Information
    recipient_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_addresses"
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["user", "address_type"]),
        ]
        unique_together = [["user", "address_type", "is_default"]]

    def __str__(self):
        return f"{self.get_address_type_display()} for {self.user.email}"

    def save(self, *args, **kwargs):
        """Ensure only one default address per type per user."""
        if self.is_default:
            # Remove default from other addresses of same type
            UserAddress.objects.filter(
                user=self.user,
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        """Return formatted full address."""
        address_parts = [self.street_address]
        
        if self.apartment_number:
            address_parts.append(f"Apt {self.apartment_number}")
            
        address_parts.extend([
            self.city,
            f"{self.state_province} {self.postal_code}",
            self.country
        ])
        
        return ", ".join(address_parts)
