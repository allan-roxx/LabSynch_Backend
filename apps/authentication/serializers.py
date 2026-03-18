"""
Serializers for authentication endpoints.

These handle input validation only — business logic lives in services.py.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.users.models import SchoolProfile, User


class RegisterSerializer(serializers.Serializer):
    """Validate registration input for SCHOOL users."""

    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        validators=[validate_password],
    )
    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False, default="")
    school_name = serializers.CharField(max_length=255)
    registration_number = serializers.CharField(
        max_length=100, required=False, default=""
    )


class LoginSerializer(serializers.Serializer):
    """Validate login credentials."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class EmailVerificationSerializer(serializers.Serializer):
    """Validate email verification token data."""

    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Validate password reset request (email only)."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validate password reset confirmation data."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        validators=[validate_password],
    )


class LogoutSerializer(serializers.Serializer):
    """Validate logout request (refresh token)."""

    refresh = serializers.CharField()


class UserResponseSerializer(serializers.ModelSerializer):
    """Serialize user data for API responses."""

    school_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "user_type",
            "is_verified",
            "school_profile",
            "created_at",
        ]

    def get_school_profile(self, obj):
        if obj.user_type != "SCHOOL":
            return None
        try:
            profile = obj.school_profile
            return {
                "id": str(profile.id),
                "school_name": profile.school_name,
                "registration_number": profile.registration_number,
                "physical_address": profile.physical_address,
                "county": profile.county,
                "contact_person": profile.contact_person,
                "contact_designation": profile.contact_designation,
                "account_status": profile.account_status,
            }
        except SchoolProfile.DoesNotExist:
            return None
