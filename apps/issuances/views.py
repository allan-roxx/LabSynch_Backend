"""
Views for Issuances and Returns.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from common.utils import success_response
from .models import EquipmentIssuance, EquipmentReturn
from .serializers import (
    EquipmentIssuanceCreateSerializer,
    EquipmentIssuanceReadSerializer,
    EquipmentReturnCreateSerializer,
    EquipmentReturnReadSerializer,
)
from .services import issue_equipment, return_equipment


class EquipmentIssuanceViewSet(viewsets.ModelViewSet):
    """
    CRUD for Issuances.
    ADMINs can create and view all. SCHOOL users can view their own.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EquipmentIssuance.objects.select_related("booking", "issued_by", "received_by")
        if self.request.user.user_type == "ADMIN":
            return queryset
        return queryset.filter(booking__school_profile__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return EquipmentIssuanceCreateSerializer
        return EquipmentIssuanceReadSerializer

    def create(self, request, *args, **kwargs):
        if request.user.user_type != "ADMIN":
            return success_response(
                data=None, 
                message="Only administrators can issue equipment.", 
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        issuance = issue_equipment(
            booking=serializer.validated_data["booking"],
            issued_by=request.user,
            received_by=serializer.validated_data["received_by"],
            issue_notes=serializer.validated_data.get("issue_notes", ""),
            issue_photo_url=serializer.validated_data.get("issue_photo_url", ""),
        )

        read_serializer = EquipmentIssuanceReadSerializer(issuance)
        return success_response(
            data=read_serializer.data,
            message="Equipment issued successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class EquipmentReturnViewSet(viewsets.ModelViewSet):
    """
    CRUD for Returns.
    ADMINs can create and view all. SCHOOL users can view their own.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EquipmentReturn.objects.select_related("booking", "received_by", "returned_by")
        if self.request.user.user_type == "ADMIN":
            return queryset
        return queryset.filter(booking__school_profile__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return EquipmentReturnCreateSerializer
        return EquipmentReturnReadSerializer

    def create(self, request, *args, **kwargs):
        if request.user.user_type != "ADMIN":
            return success_response(
                data=None, 
                message="Only administrators can receive returned equipment.", 
                status_code=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return_record = return_equipment(
            booking=serializer.validated_data["booking"],
            received_by=request.user,
            returned_by=serializer.validated_data["returned_by"],
            return_notes=serializer.validated_data.get("return_notes", ""),
            return_photo_url=serializer.validated_data.get("return_photo_url", ""),
            has_damage=serializer.validated_data.get("has_damage", False),
        )

        read_serializer = EquipmentReturnReadSerializer(return_record)
        return success_response(
            data=read_serializer.data,
            message="Equipment returned successfully.",
            status_code=status.HTTP_201_CREATED,
        )
