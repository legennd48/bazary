"""
Authentication serializers.
"""

from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    User,
    UserActivity,
    UserAddress,
    UserProfile,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "is_verified",
            "date_of_birth",
            "avatar",
            "date_joined",
            "last_login",
            "is_active",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_verified"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone_number",
        ]

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        """Create user with encrypted password."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Send verification email after registration
        from .utils import create_email_verification_token, send_verification_email

        token = create_email_verification_token(user)
        send_verification_email(user, token)

        return user


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile management."""

    full_name = serializers.CharField(read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "avatar",
            "full_name",
            "is_profile_complete",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "username", "email", "date_joined", "last_login"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        """Validate password change."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


# Enhanced Serializers for User Management Features


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile management."""

    completion_percentage = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = [
            "bio",
            "gender",
            "website",
            "location",
            "timezone",
            "language",
            "notification_preference",
            "is_profile_public",
            "show_email",
            "show_phone",
            "marketing_emails",
            "product_updates",
            "newsletter",
            "completion_percentage",
            "login_count",
            "last_activity",
        ]
        read_only_fields = ["login_count", "last_activity"]


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for user addresses."""

    full_address = serializers.ReadOnlyField()

    class Meta:
        model = UserAddress
        fields = [
            "id",
            "address_type",
            "is_default",
            "street_address",
            "apartment_number",
            "city",
            "state_province",
            "postal_code",
            "country",
            "recipient_name",
            "phone_number",
            "full_address",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        """Create address for current user."""
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class EnhancedUserSerializer(serializers.ModelSerializer):
    """Enhanced serializer for User model with profile information."""

    profile = UserProfileSerializer(read_only=True)
    addresses = UserAddressSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()
    is_profile_complete = serializers.ReadOnlyField()
    is_account_locked = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "date_of_birth",
            "avatar",
            "role",
            "is_verified",
            "is_email_verified",
            "full_name",
            "is_profile_complete",
            "is_account_locked",
            "failed_login_attempts",
            "last_password_change",
            "date_joined",
            "last_login",
            "is_active",
            "profile",
            "addresses",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
            "is_verified",
            "is_email_verified",
            "failed_login_attempts",
            "last_password_change",
        ]


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""

    token = serializers.CharField(max_length=100)

    def validate_token(self, value):
        """Validate verification token."""
        try:
            token = EmailVerificationToken.objects.get(token=value)
            if not token.is_valid:
                raise serializers.ValidationError("Invalid or expired token.")
            return value
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer for resending email verification."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists and is not verified."""
        try:
            user = User.objects.get(email=value)
            if user.is_email_verified:
                raise serializers.ValidationError("Email is already verified.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        try:
            User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""

    token = serializers.CharField(max_length=100)
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        """Validate password reset."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def validate_token(self, value):
        """Validate reset token."""
        try:
            token = PasswordResetToken.objects.get(token=value)
            if not token.is_valid:
                raise serializers.ValidationError("Invalid or expired token.")
            return value
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activity tracking."""

    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = UserActivity
        fields = [
            "id",
            "action",
            "action_display",
            "description",
            "ip_address",
            "timestamp",
            "metadata",
        ]
        read_only_fields = ["id", "timestamp"]


class AdminUserManagementSerializer(serializers.ModelSerializer):
    """Admin serializer for user management with additional fields."""

    profile = UserProfileSerializer(read_only=True)
    recent_activities = serializers.SerializerMethodField()
    account_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "is_email_verified",
            "failed_login_attempts",
            "account_locked_until",
            "last_password_change",
            "date_joined",
            "last_login",
            "profile",
            "recent_activities",
            "account_status",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
            "failed_login_attempts",
            "account_locked_until",
            "last_password_change",
        ]

    def get_recent_activities(self, obj):
        """Get recent user activities."""
        activities = obj.activities.all()[:5]
        return UserActivitySerializer(activities, many=True).data

    def get_account_status(self, obj):
        """Get account status information."""
        return {
            "is_locked": obj.is_account_locked,
            "is_verified": obj.is_email_verified,
            "profile_complete": obj.is_profile_complete,
            "failed_attempts": obj.failed_login_attempts,
        }


class BulkUserActionSerializer(serializers.Serializer):
    """Serializer for bulk user actions."""

    ACTION_CHOICES = [
        ("activate", "Activate"),
        ("deactivate", "Deactivate"),
        ("verify_email", "Verify Email"),
        ("reset_failed_attempts", "Reset Failed Login Attempts"),
        ("send_verification", "Send Email Verification"),
    ]

    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(max_length=255, required=False)

    def validate_user_ids(self, value):
        """Validate that all user IDs exist."""
        existing_users = User.objects.filter(id__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("Some user IDs do not exist.")
        return value
