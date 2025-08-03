"""
User authentication models.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with additional fields.
    """

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
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
        return bool(self.first_name and self.last_name and self.phone_number)
