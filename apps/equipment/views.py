"""
Views for Equipment app.
All responses must use the common envelope.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import action

from apps.bookings.serializers import AvailabilityCheckSerializer
from apps.bookings.services import get_available_quantity
from common.permissions import IsAdminUser
from common.utils import success_response
from .models import Equipment, EquipmentCategory, PricingRule, TransportZone
from .serializers import (
    EquipmentCategorySerializer,
    EquipmentReadSerializer,
    EquipmentWriteSerializer,
    PricingRuleSerializer,
    TransportZoneSerializer,
)
from .services import create_equipment, deactivate_equipment, update_equipment


class TransportZoneViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Transport Zones.
    All authenticated users can read, ADMIN users can write.
    """

    queryset = TransportZone.objects.all()
    serializer_class = TransportZoneSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Transport zones retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Transport zone retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Transport zone created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Transport zone updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Transport zone deleted successfully.", status_code=status.HTTP_200_OK)


class EquipmentCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD API for EquipmentCategory.
    SCHOOL users can read, ADMIN users can write.
    """

    queryset = EquipmentCategory.objects.all()
    serializer_class = EquipmentCategorySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Categories retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Category retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return success_response(
            data=serializer.data,
            message="Category created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return success_response(data=serializer.data, message="Category updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Category deleted successfully.", status_code=status.HTTP_200_OK)


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Equipment.
    SCHOOL users can read active items, ADMIN users can write and see all.
    """

    def get_queryset(self):
        queryset = Equipment.objects.select_related("category").prefetch_related("images")
        if getattr(self.request.user, "user_type", None) != "ADMIN":
            return queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return EquipmentReadSerializer
        return EquipmentWriteSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "availability"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Equipment catalog retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Equipment details retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Delegate to service
        equipment = create_equipment(**serializer.validated_data)
        read_serializer = EquipmentReadSerializer(equipment)
        return success_response(
            data=read_serializer.data,
            message="Equipment created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # Delegate to service
        equipment = update_equipment(instance, **serializer.validated_data)
        read_serializer = EquipmentReadSerializer(equipment)
        return success_response(
            data=read_serializer.data,
            message="Equipment updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete using service
        deactivate_equipment(instance)
        return success_response(message="Equipment deactivated successfully.", status_code=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def availability(self, request, pk=None):
        """
        Check real-time availability for this equipment between pickup and return dates.
        """
        instance = self.get_object()
        serializer = AvailabilityCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        available_qty = get_available_quantity(
            equipment_id=str(instance.id),
            start_date=serializer.validated_data["pickup_date"],
            end_date=serializer.validated_data["return_date"]
        )
        
        return success_response(
            data={"equipment_id": instance.id, "available_quantity": available_qty},
            message="Availability checked successfully."
        )


class PricingRuleViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Pricing Rules. ADMIN only.
    """

    queryset = PricingRule.objects.all()
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Pricing rules retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Pricing rule retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(
            data=serializer.data,
            message="Pricing rule created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message="Pricing rule updated successfully.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Pricing rule deleted successfully.", status_code=status.HTTP_200_OK)
