"""
Business logic for the Users app.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import SchoolProfile, User

logger = logging.getLogger(__name__)


@transaction.atomic
def update_user_profile(user: User, **kwargs) -> User:
    """
    Update a user's own basic profile fields (full_name, phone_number).
    Only the listed fields can be changed; all others are silently ignored.
    """
    allowed = {"full_name", "phone_number"}
    update_fields = ["updated_at"]
    for field, value in kwargs.items():
        if field in allowed:
            setattr(user, field, value)
            update_fields.append(field)
    user.save(update_fields=update_fields)
    logger.info("Profile updated for user %s", user.email)
    return user


@transaction.atomic
def update_school_profile(profile: SchoolProfile, data: dict) -> SchoolProfile:
    """
    Allow a SCHOOL user to update non-sensitive profile fields.
    Excludes account_status, credit_limit, and registration_number.
    """
    allowed = {
        "school_name",
        "physical_address",
        "county",
        "contact_person",
        "contact_designation",
    }
    update_fields = ["updated_at"]
    for field, value in data.items():
        if field in allowed:
            setattr(profile, field, value)
            update_fields.append(field)
    profile.save(update_fields=update_fields)
    return profile


@transaction.atomic
def admin_update_school_profile(profile: SchoolProfile, data: dict) -> SchoolProfile:
    """
    Allow an ADMIN to update any school profile field including
    account_status, credit_limit, and registration_number.
    """
    allowed = {
        "school_name",
        "registration_number",
        "physical_address",
        "county",
        "contact_person",
        "contact_designation",
        "credit_limit",
        "account_status",
    }
    update_fields = ["updated_at"]
    for field, value in data.items():
        if field in allowed:
            setattr(profile, field, value)
            update_fields.append(field)
    profile.save(update_fields=update_fields)
    logger.info("Admin updated school profile %s", profile.id)
    return profile


def change_password(user: User, old_password: str, new_password: str) -> User:
    """
    Change a user's password after verifying the current one.
    Raises ValidationError if old_password is incorrect.
    """
    if not user.check_password(old_password):
        raise ValidationError({"old_password": "Current password is incorrect."})
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    logger.info("Password changed for user %s", user.email)
    return user
