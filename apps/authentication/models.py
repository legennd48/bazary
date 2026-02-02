"""
User authentication models.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager that uses email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # Set username to email for AbstractUser compatibility
        extra_fields.setdefault("username", email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "super_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with additional fields.
    """

    USER_ROLES = [
        ("customer", "Customer"),
        ("vendor", "Vendor"),
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

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

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
        if hasattr(self, "profile"):
            return basic_complete and self.profile.completion_percentage >= 70
        return basic_complete

    @property
    def is_account_locked(self):
        """Check if account is currently locked."""
        if not self.account_locked_until:
            return False
        return timezone.now() < self.account_locked_until

    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary."""
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
            "vendor": 2,
            "staff": 3,
            "admin": 4,
            "super_admin": 5,
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(role, 0)
        return user_level >= required_level

    @property
    def is_vendor(self):
        """Check if user is a vendor."""
        return hasattr(self, 'vendor_profile')


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
    location = models.CharField(max_length=100, blank=True, help_text="User's location")

    # Preferences
    timezone = models.CharField(
        max_length=50, default="UTC", help_text="User's preferred timezone"
    )
    language = models.CharField(
        max_length=10, default="en", help_text="User's preferred language"
    )
    notification_preference = models.CharField(
        max_length=10,
        choices=NOTIFICATION_PREFERENCES,
        default="email",
        help_text="Preferred notification method",
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
    newsletter = models.BooleanField(default=False, help_text="Subscribe to newsletter")

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
                user=self.user, address_type=self.address_type, is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_address(self):
        """Return formatted full address."""
        address_parts = [self.street_address]

        if self.apartment_number:
            address_parts.append(f"Apt {self.apartment_number}")

        address_parts.extend(
            [self.city, f"{self.state_province} {self.postal_code}", self.country]
        )

        return ", ".join(address_parts)


class EmailVerificationToken(models.Model):
    """
    Token for email verification.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "email_verification_tokens"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Verification token for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 24 hours
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired

    def use_token(self):
        """Mark token as used."""
        self.is_used = True
        self.save()


class PasswordResetToken(models.Model):
    """
    Token for password reset.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expires in 1 hour
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired

    def use_token(self):
        """Mark token as used."""
        self.is_used = True
        self.save()


class UserActivity(models.Model):
    """
    Track user activity for audit purposes.
    """

    ACTION_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("password_change", "Password Change"),
        ("password_reset", "Password Reset"),
        ("email_verification", "Email Verification"),
        ("profile_update", "Profile Update"),
        ("avatar_upload", "Avatar Upload"),
        ("account_activation", "Account Activation"),
        ("account_deactivation", "Account Deactivation"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_activities"
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.timestamp}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)


# ============================================================================
# Vendor Models for Multi-Vendor Marketplace
# ============================================================================


class Vendor(models.Model):
    """
    Vendor/Seller model for multi-vendor marketplace.
    A vendor is a user who can sell products and/or offer services.
    """

    VERIFICATION_STATUS = [
        ('pending', 'Pending Review'),
        ('documents_required', 'Documents Required'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    VENDOR_TYPE = [
        ('individual', 'Individual Seller'),
        ('business', 'Business'),
        ('service_provider', 'Service Provider'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
    )

    # Store/Business Information
    store_name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    store_description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendors/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='vendors/banners/', null=True, blank=True)

    # Business Details
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE, default='individual')
    business_name = models.CharField(max_length=255, blank=True, help_text="Legal business name")
    business_registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True, help_text="Tax identification number")

    # Contact Information
    business_email = models.EmailField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)

    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Ethiopia')

    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    verification_notes = models.TextField(blank=True, help_text="Admin notes on verification")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_vendors'
    )

    # Commission and Payments
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text="Platform commission percentage"
    )
    payout_method = models.CharField(max_length=50, blank=True)
    payout_details = models.JSONField(default=dict, blank=True)

    # Settings
    is_active = models.BooleanField(default=False, help_text="Can the vendor sell?")
    is_featured = models.BooleanField(default=False)
    accepts_returns = models.BooleanField(default=True)
    return_policy = models.TextField(blank=True)
    shipping_policy = models.TextField(blank=True)

    # Statistics (denormalized for performance)
    total_products = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.store_name)
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Vendor.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def is_verified(self):
        return self.verification_status == 'verified'

    @property
    def can_sell(self):
        return self.is_active and self.is_verified


class VendorDocument(models.Model):
    """
    Documents uploaded by vendors for verification.
    """

    DOCUMENT_TYPES = [
        ('id_front', 'ID Card (Front)'),
        ('id_back', 'ID Card (Back)'),
        ('business_license', 'Business License'),
        ('tax_certificate', 'Tax Certificate'),
        ('bank_statement', 'Bank Statement'),
        ('other', 'Other Document'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='vendors/documents/')
    description = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_documents'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.store_name} - {self.get_document_type_display()}"


class VendorApplication(models.Model):
    """
    Track vendor application process.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_applications'
    )

    # Application Data
    store_name = models.CharField(max_length=255)
    vendor_type = models.CharField(max_length=20, choices=Vendor.VENDOR_TYPE)
    business_description = models.TextField()
    product_categories = models.JSONField(default=list, help_text="Categories vendor plans to sell in")
    expected_monthly_sales = models.CharField(max_length=50, blank=True)

    # Contact
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)

    # Admin handling
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Resulting vendor profile
    vendor = models.OneToOneField(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendor_applications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.store_name} - {self.get_status_display()}"

