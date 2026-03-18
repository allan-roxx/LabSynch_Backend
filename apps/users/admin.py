from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import SchoolProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""

    list_display = (
        "email",
        "full_name",
        "user_type",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = ("user_type", "is_verified", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone_number")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("full_name", "phone_number", "user_type")},
        ),
        (
            "Verification",
            {"fields": ("is_verified", "email_verified_at")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Timestamps", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "user_type",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    """Admin configuration for the SchoolProfile model."""

    list_display = (
        "school_name",
        "user",
        "registration_number",
        "county",
        "account_status",
        "credit_limit",
    )
    list_filter = ("account_status", "county")
    search_fields = ("school_name", "registration_number", "user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
