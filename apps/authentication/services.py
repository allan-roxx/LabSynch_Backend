"""
Authentication business logic.

All auth-related operations live here — views only delegate to these functions.
"""

import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.models import AccountStatus, SchoolProfile, User, UserType

logger = logging.getLogger(__name__)


@transaction.atomic
def register_school_user(
    email,
    password,
    full_name,
    phone_number="",
    school_name="",
    registration_number="",
):
    """
    Register a new SCHOOL user with an associated SchoolProfile.

    Steps:
      1. Validate email uniqueness
      2. Create User record (is_verified=False)
      3. Create SchoolProfile
      4. Send verification email
      5. Return the user

    Raises:
        ValidationError: on duplicate email or validation failure.
    """
    # Check email uniqueness
    if User.objects.filter(email__iexact=email).exists():
        raise ValidationError({"email": "A user with this email already exists."})

    # Create user
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone_number=phone_number,
        user_type=UserType.SCHOOL,
        is_verified=False,
    )

    # Create school profile
    SchoolProfile.objects.create(
        user=user,
        school_name=school_name,
        registration_number=registration_number,
    )

    # Send verification email (non-blocking; failure logged, not raised)
    try:
        send_verification_email(user)
    except Exception as exc:
        logger.error(
            "Failed to send verification email to %s: %s",
            user.email,
            str(exc),
            exc_info=True,
        )

    logger.info("School user registered: %s (id=%s)", user.email, user.id)
    return user


def send_verification_email(user):
    """
    Generate a verification token and send a verification email.

    Uses Django's built-in token generator for secure, one-time tokens.
    """
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = default_token_generator.make_token(user)
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    verification_link = f"{frontend_url}/verify-email?uid={uid}&token={token}"

    subject = "LabSynch — Verify Your Email Address"
    message = (
        f"Hello {user.full_name},\n\n"
        f"Thank you for registering with LabSynch.\n"
        f"Please verify your email by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"If you did not register, please ignore this email.\n\n"
        f"— The LabSynch Team"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Verification email sent to %s", user.email)


def verify_email(uid, token):
    """
    Verify a user's email using the uid + token from the verification link.

    Raises:
        ValidationError: on invalid/expired token.
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({"token": "Invalid verification link."})

    if user.is_verified:
        raise ValidationError({"token": "Email is already verified."})

    if not default_token_generator.check_token(user, token):
        raise ValidationError({"token": "Invalid or expired verification token."})

    user.is_verified = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=["is_verified", "email_verified_at", "updated_at"])

    logger.info("Email verified for user %s (id=%s)", user.email, user.id)
    return user


def login_user(email, password):
    """
    Authenticate a user and return JWT tokens.

    Checks:
      - Valid credentials
      - Email is verified
      - Account is active (for SCHOOL users, checks SchoolProfile.account_status)

    Returns:
        dict: {user, tokens: {access, refresh}}

    Raises:
        ValidationError: on invalid credentials, unverified email, or suspended account.
    """
    user = authenticate(email=email, password=password)

    if user is None:
        raise ValidationError(
            {"non_field_errors": "Invalid email or password."}
        )

    if not user.is_verified:
        raise ValidationError(
            {"non_field_errors": "Please verify your email before logging in."}
        )

    # For SCHOOL users, check account status
    if user.user_type == UserType.SCHOOL:
        try:
            profile = user.school_profile
            if profile.account_status != AccountStatus.ACTIVE:
                raise ValidationError(
                    {
                        "non_field_errors": (
                            f"Your account is {profile.account_status.lower()}. "
                            "Please contact support."
                        )
                    }
                )
        except SchoolProfile.DoesNotExist:
            pass  # Should not happen, but be defensive

    # Update last_login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    tokens = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

    logger.info("User logged in: %s (id=%s)", user.email, user.id)
    return {"user": user, "tokens": tokens}


def logout_user(refresh_token):
    """
    Blacklist the given refresh token to log the user out.

    Raises:
        ValidationError: on invalid/already blacklisted token.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        raise ValidationError(
            {"refresh": "Token is invalid or already blacklisted."}
        )

    logger.info("User logged out (token blacklisted)")


def request_password_reset(email):
    """
    Send a password reset email if the user exists.

    For security, always return success even if the email is not found.
    """
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Don't reveal whether the email exists
        logger.info("Password reset requested for non-existent email: %s", email)
        return

    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = default_token_generator.make_token(user)
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?uid={uid}&token={token}"

    subject = "LabSynch — Password Reset Request"
    message = (
        f"Hello {user.full_name},\n\n"
        f"We received a request to reset your password.\n"
        f"Click the link below to set a new password:\n\n"
        f"{reset_link}\n\n"
        f"If you did not request a password reset, ignore this email.\n\n"
        f"— The LabSynch Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Password reset email sent to %s", user.email)
    except Exception as exc:
        logger.error(
            "Failed to send password reset email to %s: %s",
            user.email,
            str(exc),
            exc_info=True,
        )


def reset_password(uid, token, new_password):
    """
    Reset a user's password using the uid + token from the reset email.

    Raises:
        ValidationError: on invalid/expired token.
    """
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({"token": "Invalid password reset link."})

    if not default_token_generator.check_token(user, token):
        raise ValidationError({"token": "Invalid or expired reset token."})

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    # Blacklist all outstanding tokens for this user
    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    for ot in outstanding_tokens:
        try:
            BlacklistedToken.objects.get_or_create(token=ot)
        except Exception:
            pass

    logger.info("Password reset for user %s (id=%s)", user.email, user.id)
    return user
