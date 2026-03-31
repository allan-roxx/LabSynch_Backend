"""
Views for Damages app.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action

from common.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from common.utils import success_response
from .models import DamageReport
from .serializers import (
    DamageReportCreateSerializer,
    DamageReportReadSerializer,
    DamageReportResolveSerializer,
)
from .services import create_damage_report, resolve_damage_report


@extend_schema_view(
    list=extend_schema(responses={200: DamageReportReadSerializer(many=True)}, summary="List all damage reports"),
    retrieve=extend_schema(responses={200: DamageReportReadSerializer}, summary="Get a damage report"),
    create=extend_schema(request=DamageReportCreateSerializer, responses={201: DamageReportReadSerializer}, summary="Create damage report"),
    update=extend_schema(request=DamageReportCreateSerializer, responses={200: DamageReportReadSerializer}, summary="Update damage report"),
    partial_update=extend_schema(request=DamageReportCreateSerializer, responses={200: DamageReportReadSerializer}, summary="Partial update damage report"),
    destroy=extend_schema(summary="Delete damage report"),
)
class DamageReportViewSet(viewsets.ModelViewSet):
    """
    CRUD for Damage Reports.
    Strictly restricted to ADMIN users.
    """
    permission_classes = [IsAdminUser]
    queryset = DamageReport.objects.select_related(
        "equipment_return", 
        "booking_item", 
        "reported_by"
    )

    def get_serializer_class(self):
        if self.action == "create":
            return DamageReportCreateSerializer
        return DamageReportReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = create_damage_report(
            equipment_return=serializer.validated_data["equipment_return"],
            booking_item=serializer.validated_data["booking_item"],
            reported_by=request.user,
            quantity_damaged=serializer.validated_data.get("quantity_damaged", 1),
            severity=serializer.validated_data.get("severity", "MINOR"),
            description=serializer.validated_data["description"],
            photo_urls=serializer.validated_data.get("photo_urls", []),
        )

        read_serializer = DamageReportReadSerializer(report)
        return success_response(
            data=read_serializer.data,
            message="Damage report created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        request=DamageReportResolveSerializer,
        responses={200: DamageReportReadSerializer},
        summary="Resolve a damage report (set resolution status + repair cost)",
    )
    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = self.get_object()
        serializer = DamageReportResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_report = resolve_damage_report(
            damage_report=report,
            resolution_status=serializer.validated_data["resolution_status"],
            repair_cost=serializer.validated_data.get("repair_cost")
        )
        
        read_serializer = DamageReportReadSerializer(updated_report)
        return success_response(
            data=read_serializer.data,
            message="Damage report resolution updated.",
            status_code=status.HTTP_200_OK,
        )
