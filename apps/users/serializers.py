"""
Serializers for the Users app.
"""

from rest_framework import serializers

from .models import SchoolProfile, User


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "user_type",
            "is_verified",
            "email_verified_at",
            "created_at",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone_number"]
        extra_kwargs = {
            "full_name": {"required": False},
            "phone_number": {"required": False},
        }


class SchoolProfileReadSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = SchoolProfile
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "school_name",
            "registration_number",
            "physical_address",
            "county",
            "contact_person",
            "contact_designation",
            "credit_limit",
            "account_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "user_email", "user_full_name", "created_at", "updated_at"]


class SchoolProfileUpdateSerializer(serializers.ModelSerializer):
    """For SCHOOL users updating their own non-sensitive profile fields."""

    class Meta:
        model = SchoolProfile
        fields = [
            "school_name",
            "physical_address",
            "county",
            "contact_person",
            "contact_designation",
        ]


class AdminSchoolProfileUpdateSerializer(serializers.ModelSerializer):
    """For ADMIN updating a school — includes status and financial fields."""

    class Meta:
        model = SchoolProfile
        fields = [
            "school_name",
            "registration_number",
            "physical_address",
            "county",
            "contact_person",
            "contact_designation",
            "credit_limit",
            "account_status",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "New passwords do not match."}
            )
        return attrs
