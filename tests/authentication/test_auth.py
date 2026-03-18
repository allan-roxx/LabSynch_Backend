"""
Tests for authentication endpoints.

Covers: registration, duplicate email, login, invalid credentials,
email verification, token refresh, logout.
"""

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User, UserType
from tests.factories import SchoolProfileFactory, UserFactory


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def school_user(db):
    """Create a verified school user with a profile."""
    user = UserFactory(
        email="school@example.com",
        user_type=UserType.SCHOOL,
        is_verified=True,
    )
    user.set_password("TestPass123!")
    user.save()
    SchoolProfileFactory(user=user, school_name="Test Academy")
    return user


@pytest.fixture
def unverified_user(db):
    """Create an unverified school user."""
    user = UserFactory(
        email="unverified@example.com",
        user_type=UserType.SCHOOL,
        is_verified=False,
    )
    user.set_password("TestPass123!")
    user.save()
    SchoolProfileFactory(user=user, school_name="Unverified School")
    return user


# ==========================================================================
# Registration Tests
# ==========================================================================


@pytest.mark.django_db
class TestRegistration:
    """Tests for POST /api/auth/register/"""

    url = reverse("auth-register")

    def test_successful_registration(self, api_client):
        """A new school user should be created with a SchoolProfile."""
        payload = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "full_name": "Jane Doe",
            "phone_number": "+254712345678",
            "school_name": "Nairobi Academy",
            "registration_number": "REG-001",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["email"] == "newuser@example.com"
        assert response.data["data"]["user_type"] == "SCHOOL"
        assert response.data["data"]["is_verified"] is False

        # Verify user exists in DB
        user = User.objects.get(email="newuser@example.com")
        assert user.user_type == UserType.SCHOOL
        assert hasattr(user, "school_profile")
        assert user.school_profile.school_name == "Nairobi Academy"

    def test_duplicate_email_registration(self, api_client, school_user):
        """Registration with an existing email should fail."""
        payload = {
            "email": school_user.email,
            "password": "StrongPass123!",
            "full_name": "Another User",
            "school_name": "Another School",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_invalid_email_format(self, api_client):
        """Registration with invalid email format should fail."""
        payload = {
            "email": "not-an-email",
            "password": "StrongPass123!",
            "full_name": "Test User",
            "school_name": "Test School",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_weak_password_rejected(self, api_client):
        """Registration with a weak password should fail validation."""
        payload = {
            "email": "weak@example.com",
            "password": "123",
            "full_name": "Test User",
            "school_name": "Test School",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


# ==========================================================================
# Login Tests
# ==========================================================================


@pytest.mark.django_db
class TestLogin:
    """Tests for POST /api/auth/login/"""

    url = reverse("auth-login")

    def test_successful_login(self, api_client, school_user):
        """A verified user with correct credentials should get JWT tokens."""
        payload = {
            "email": school_user.email,
            "password": "TestPass123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "tokens" in response.data["data"]
        assert "access" in response.data["data"]["tokens"]
        assert "refresh" in response.data["data"]["tokens"]

    def test_invalid_credentials(self, api_client, school_user):
        """Login with wrong password should fail with 400."""
        payload = {
            "email": school_user.email,
            "password": "WrongPassword!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_unverified_email_login(self, api_client, unverified_user):
        """Login with unverified email should fail."""
        payload = {
            "email": unverified_user.email,
            "password": "TestPass123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_nonexistent_user_login(self, api_client):
        """Login with a non-existent email should fail."""
        payload = {
            "email": "nobody@example.com",
            "password": "TestPass123!",
        }
        response = api_client.post(self.url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


# ==========================================================================
# Email Verification Tests
# ==========================================================================


@pytest.mark.django_db
class TestEmailVerification:
    """Tests for POST /api/auth/verify-email/"""

    url = reverse("auth-verify-email")

    def test_successful_verification(self, api_client, unverified_user):
        """Verify email with a valid token should succeed."""
        uid = urlsafe_base64_encode(force_bytes(str(unverified_user.pk)))
        token = default_token_generator.make_token(unverified_user)

        response = api_client.post(
            self.url,
            {"uid": uid, "token": token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        unverified_user.refresh_from_db()
        assert unverified_user.is_verified is True
        assert unverified_user.email_verified_at is not None

    def test_invalid_token(self, api_client, unverified_user):
        """Invalid token should fail."""
        uid = urlsafe_base64_encode(force_bytes(str(unverified_user.pk)))

        response = api_client.post(
            self.url,
            {"uid": uid, "token": "invalid-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False


# ==========================================================================
# Token Refresh Tests
# ==========================================================================


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for POST /api/auth/token/refresh/"""

    url = reverse("auth-token-refresh")

    def test_token_refresh(self, api_client, school_user):
        """Valid refresh token should return new access token."""
        # First login to get tokens
        login_response = api_client.post(
            reverse("auth-login"),
            {"email": school_user.email, "password": "TestPass123!"},
            format="json",
        )
        refresh_token = login_response.data["data"]["tokens"]["refresh"]

        # Refresh
        response = api_client.post(
            self.url,
            {"refresh": refresh_token},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK


# ==========================================================================
# Logout Tests
# ==========================================================================


@pytest.mark.django_db
class TestLogout:
    """Tests for POST /api/auth/logout/"""

    url = reverse("auth-logout")

    def test_successful_logout(self, api_client, school_user):
        """Logout should blacklist the refresh token."""
        # Login first
        login_response = api_client.post(
            reverse("auth-login"),
            {"email": school_user.email, "password": "TestPass123!"},
            format="json",
        )
        tokens = login_response.data["data"]["tokens"]

        # Authenticate for logout
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = api_client.post(
            self.url,
            {"refresh": tokens["refresh"]},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    def test_logout_requires_authentication(self, api_client):
        """Logout without token should fail with 401."""
        response = api_client.post(
            self.url,
            {"refresh": "some-token"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
