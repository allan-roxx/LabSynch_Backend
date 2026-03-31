"""
Views for the Users app.

Endpoints:
  GET   /api/users/me/                    — own profile (any authenticated user)
  PATCH /api/users/me/                    — update own basic info
  GET   /api/users/me/school-profile/     — SCHOOL user's own school profile
  PATCH /api/users/me/school-profile/     — SCHOOL user updates own school profile
  POST  /api/users/change-password/       — change own password
  GET   /api/users/                       — ADMIN: list all users
  GET   /api/users/<id>/                  — ADMIN: retrieve any user
  GET   /api/school-profiles/             — ADMIN: list all school profiles
  GET   /api/school-profiles/<id>/        — ADMIN: retrieve a school profile
  PATCH /api/school-profiles/<id>/        — ADMIN: update school profile (status/credit)
"""

import logging

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.pagination import StandardResultsPagination
from common.permissions import IsAdminUser, IsSchoolUser
from common.utils import success_response

from .models import SchoolProfile, User
from .serializers import (
    AdminSchoolProfileUpdateSerializer,
    ChangePasswordSerializer,
    SchoolProfileReadSerializer,
    SchoolProfileUpdateSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
)
from .services import (
    admin_update_school_profile,
    change_password,
    update_school_profile,
    update_user_profile,
)

logger = logging.getLogger(__name__)


@extend_schema(
    methods=["GET"],
    responses={200: UserReadSerializer},
    summary="Get own profile",
)
@extend_schema(
    methods=["PATCH"],
    request=UserUpdateSerializer,
    responses={200: UserReadSerializer},
    summary="Update own profile (full_name, phone_number)",
)
class MeView(APIView):
    """Retrieve or partially update the authenticated user's own profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            data=UserReadSerializer(request.user).data,
            message="Profile retrieved successfully.",
        )

    def patch(self, request):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(request.user, **serializer.validated_data)
        return success_response(
            data=UserReadSerializer(user).data,
            message="Profile updated successfully.",
        )


@extend_schema(
    methods=["GET"],
    responses={200: SchoolProfileReadSerializer},
    summary="Get own school profile",
)
@extend_schema(
    methods=["PATCH"],
    request=SchoolProfileUpdateSerializer,
    responses={200: SchoolProfileReadSerializer},
    summary="Update own school profile (name, address, contact fields)",
)
class MySchoolProfileView(APIView):
    """Retrieve or update the SCHOOL user's own school profile."""

    permission_classes = [IsAuthenticated, IsSchoolUser]

    def _get_profile(self, request):
        try:
            return request.user.school_profile
        except SchoolProfile.DoesNotExist:
            return None

    def get(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return success_response(
                data=None,
                message="School profile not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return success_response(
            data=SchoolProfileReadSerializer(profile).data,
            message="School profile retrieved successfully.",
        )

    def patch(self, request):
        profile = self._get_profile(request)
        if profile is None:
            return success_response(
                data=None,
                message="School profile not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        serializer = SchoolProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = update_school_profile(profile, serializer.validated_data)
        return success_response(
            data=SchoolProfileReadSerializer(profile).data,
            message="School profile updated successfully.",
        )


@extend_schema(
    request=ChangePasswordSerializer,
    responses={200: None},
    summary="Change own password",
)
class ChangePasswordView(APIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return success_response(message="Password changed successfully.")


class UserAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """ADMIN-only: list and retrieve any user account."""

    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = UserReadSerializer
    queryset = User.objects.all().order_by("-created_at")
    pagination_class = StandardResultsPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Users retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(
            data=self.get_serializer(instance).data,
            message="User retrieved successfully.",
        )


class SchoolProfileAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """ADMIN-only: list, retrieve, and update school profiles."""

    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = SchoolProfile.objects.select_related("user").all()
    pagination_class = StandardResultsPagination

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return AdminSchoolProfileUpdateSerializer
        return SchoolProfileReadSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SchoolProfileReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SchoolProfileReadSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="School profiles retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(
            data=SchoolProfileReadSerializer(instance).data,
            message="School profile retrieved successfully.",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = AdminSchoolProfileUpdateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        profile = admin_update_school_profile(instance, serializer.validated_data)
        return success_response(
            data=SchoolProfileReadSerializer(profile).data,
            message="School profile updated successfully.",
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
