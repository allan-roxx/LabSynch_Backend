"""
Views for Equipment app.
All responses must use the common envelope.
"""

import os

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser

from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.bookings.serializers import AvailabilityCheckSerializer
from apps.bookings.services import get_available_quantity
from common.exports import export_csv, export_pdf
from common.permissions import IsAdminUser
from common.utils import success_response
from .models import Equipment, EquipmentCategory, EquipmentImage, PricingRule, TransportZone
from .serializers import (
    EquipmentCategorySerializer,
    EquipmentImageSerializer,
    EquipmentImageUpdateSerializer,
    EquipmentImageUploadSerializer,
    EquipmentReadSerializer,
    EquipmentStockAppendSerializer,
    EquipmentWriteSerializer,
    PricingRuleSerializer,
    TransportZoneSerializer,
)
from .services import append_equipment_stock, create_equipment, deactivate_equipment, update_equipment


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

    filterset_fields = ("category", "condition", "is_consumable", "is_active")
    search_fields = ("equipment_name", "equipment_code", "description")
    ordering_fields = ("equipment_name", "unit_price_per_day", "available_quantity", "created_at")
    ordering = ("equipment_name",)

    @staticmethod
    def _store_image(request, equipment: Equipment, image_file) -> str:
        stem, ext = os.path.splitext(image_file.name)
        safe_stem = slugify(stem) or "image"
        filename = f"{timezone.now().strftime('%Y%m%d%H%M%S%f')}_{safe_stem}{ext.lower()}"
        path = default_storage.save(f"equipment/{equipment.id}/{filename}", image_file)
        image_url = default_storage.url(path)
        if not image_url.startswith("http"):
            image_url = request.build_absolute_uri(image_url)
        return image_url

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

    _EXPORT_HEADERS = [
        "ID", "Code", "Name", "Category", "Total Qty", "Available Qty",
        "Unit Price/Day", "Condition", "Active",
    ]

    @extend_schema(
        parameters=[OpenApiParameter("fmt", str, description="csv or pdf", default="csv")],
        responses={200: None},
        summary="Export equipment catalog as CSV or PDF (admin only)",
    )
    @action(detail=False, methods=["get"], url_path="export", url_name="export",
            permission_classes=[IsAuthenticated, IsAdminUser])
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv").lower()
        rows = [
            {
                "ID": str(eq.id),
                "Code": eq.equipment_code,
                "Name": eq.equipment_name,
                "Category": eq.category.category_name if eq.category else "",
                "Total Qty": eq.total_quantity,
                "Available Qty": eq.available_quantity,
                "Unit Price/Day": str(eq.unit_price_per_day),
                "Condition": eq.condition,
                "Active": eq.is_active,
            }
            for eq in self.filter_queryset(
                Equipment.objects.select_related("category").all()
            )
        ]
        if fmt == "pdf":
            return export_pdf("Equipment Catalog", self._EXPORT_HEADERS, rows, "equipment")
        return export_csv(self._EXPORT_HEADERS, rows, "equipment")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminUser])
    def add_stock(self, request, pk=None):
        """Append stock for a specific equipment item."""
        equipment = self.get_object()
        serializer = EquipmentStockAppendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = append_equipment_stock(
            equipment=equipment,
            additional_quantity=serializer.validated_data["additional_quantity"],
        )
        return success_response(
            data=EquipmentReadSerializer(updated).data,
            message="Equipment stock updated successfully.",
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsAdminUser],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        """Upload and append a new image to an equipment item."""
        equipment = self.get_object()
        serializer = EquipmentImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_primary = serializer.validated_data.get("is_primary", False)
        if is_primary:
            equipment.images.update(is_primary=False)

        image_url = self._store_image(request, equipment, serializer.validated_data["image"])
        image = EquipmentImage.objects.create(
            equipment=equipment,
            image_url=image_url,
            is_primary=is_primary,
            display_order=serializer.validated_data.get("display_order", 0),
        )

        return success_response(
            data=EquipmentImageSerializer(image).data,
            message="Equipment image uploaded successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAuthenticated, IsAdminUser],
        parser_classes=[MultiPartParser, FormParser],
        url_path=r"images/(?P<image_id>[^/.]+)",
    )
    def update_image(self, request, pk=None, image_id=None):
        """Replace image file or update image metadata for an equipment image."""
        equipment = self.get_object()
        image = get_object_or_404(EquipmentImage, id=image_id, equipment=equipment)

        serializer = EquipmentImageUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        update_fields = ["updated_at"]
        if "image" in validated:
            image.image_url = self._store_image(request, equipment, validated["image"])
            update_fields.append("image_url")

        if "display_order" in validated:
            image.display_order = validated["display_order"]
            update_fields.append("display_order")

        if "is_primary" in validated:
            if validated["is_primary"]:
                equipment.images.exclude(id=image.id).update(is_primary=False)
            image.is_primary = validated["is_primary"]
            update_fields.append("is_primary")

        image.save(update_fields=update_fields)
        return success_response(
            data=EquipmentImageSerializer(image).data,
            message="Equipment image updated successfully.",
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
