"""
Authentication views.

All views delegate to services.py and return responses using the
standard envelope format from common/utils.py.
"""

import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from common.utils import success_response

from .serializers import (
    EmailVerificationSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserResponseSerializer,
)
from .services import (
    login_user,
    logout_user,
    register_school_user,
    request_password_reset,
    reset_password,
    verify_email,
)

logger = logging.getLogger(__name__)


@extend_schema(
    request=RegisterSerializer,
    responses={201: UserResponseSerializer},
    summary="Register a new school account",
    tags=["auth"],
)
class RegisterView(APIView):
    """
    POST /api/auth/register/

    Register a new SCHOOL user. Creates User + SchoolProfile.
    """

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = register_school_user(**serializer.validated_data)

        return success_response(
            data=UserResponseSerializer(user).data,
            message="Registration successful. Please check your email to verify your account.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(
    request=EmailVerificationSerializer,
    responses={200: UserResponseSerializer},
    summary="Verify email address",
    tags=["auth"],
)
class EmailVerificationView(APIView):
    """
    POST /api/auth/verify-email/

    Verify a user's email address using the uid + token from the verification link.
    """

    permission_classes = [AllowAny]
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = verify_email(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
        )

        return success_response(
            data=UserResponseSerializer(user).data,
            message="Email verified successfully.",
        )


@extend_schema(
    request=LoginSerializer,
    responses={200: UserResponseSerializer},
    summary="Login — returns access + refresh JWT tokens plus user data",
    tags=["auth"],
)
class LoginView(APIView):
    """
    POST /api/auth/login/

    Authenticate a user and return JWT tokens.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        user_data = UserResponseSerializer(result["user"]).data
        user_data["tokens"] = result["tokens"]

        return success_response(
            data=user_data,
            message="Login successful.",
        )


@extend_schema(
    request=LogoutSerializer,
    responses={200: OpenApiResponse(description="Logged out successfully.")},
    summary="Logout — blacklists the refresh token",
    tags=["auth"],
)
class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklist the refresh token to log the user out.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logout_user(refresh_token=serializer.validated_data["refresh"])

        return success_response(message="Logged out successfully.")


@extend_schema(
    request=PasswordResetRequestSerializer,
    responses={200: OpenApiResponse(description="Reset email sent if account exists.")},
    summary="Request password reset email",
    tags=["auth"],
)
class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/

    Send a password reset email. Always returns 200 for security.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_password_reset(email=serializer.validated_data["email"])

        return success_response(
            message="If an account with this email exists, a password reset link has been sent.",
        )


@extend_schema(
    request=PasswordResetConfirmSerializer,
    responses={200: OpenApiResponse(description="Password reset successfully.")},
    summary="Confirm password reset with uid + token",
    tags=["auth"],
)
class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset-confirm/

    Reset the user's password using the uid + token from the reset email.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reset_password(
            uid=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )

        return success_response(
            message="Password has been reset successfully.",
        )
