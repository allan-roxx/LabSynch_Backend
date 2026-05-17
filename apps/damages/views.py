"""
Views for Damages app.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from common.exports import export_csv, export_pdf
from common.permissions import IsAdminUser, IsSchoolUser
from rest_framework.exceptions import ValidationError
from common.utils import success_response
from .models import DamageReport
from .serializers import (
    DamageReportCreateSerializer,
    DamageReportReadSerializer,
    DamageReportResolveSerializer,
    DamageReportSettleSerializer,
)
from .services import create_damage_report, resolve_damage_report, settle_damage_report_by_school


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
    permission_classes = [IsAuthenticated]
    queryset = DamageReport.objects.select_related(
        "equipment_return", 
        "equipment_return__booking",
        "equipment_return__booking__school_profile",
        "equipment_return__booking__school_profile__user",
        "booking_item", 
        "booking_item__equipment",
        "reported_by"
    )

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "resolve", "export"]:
            return [IsAuthenticated(), IsAdminUser()]
        if self.action == "settle":
            return [IsAuthenticated(), IsSchoolUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "user_type", None) == "ADMIN":
            return queryset
        return queryset.filter(equipment_return__booking__school_profile__user=self.request.user)

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
            repair_cost=serializer.validated_data.get("repair_cost"),
            amount_paid=serializer.validated_data.get("amount_paid"),
        )
        
        read_serializer = DamageReportReadSerializer(updated_report)
        return success_response(
            data=read_serializer.data,
            message="Damage report resolution updated.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        request=DamageReportSettleSerializer,
        responses={200: DamageReportReadSerializer},
        summary="School settles own damage liability",
    )
    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        report = self.get_object()
        serializer = DamageReportSettleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_report = settle_damage_report_by_school(
            damage_report=report,
            school_user=request.user,
            amount_paid=serializer.validated_data.get("amount_paid"),
        )

        read_serializer = DamageReportReadSerializer(updated_report)
        return success_response(
            data=read_serializer.data,
            message="Liability payment recorded successfully.",
            status_code=status.HTTP_200_OK,
        )

    _EXPORT_HEADERS = [
        "ID", "Booking Ref", "Equipment", "Severity", "Qty Damaged",
        "Repair Cost", "Amount Paid", "Resolution Status", "Created At",
    ]

    @extend_schema(
        parameters=[OpenApiParameter("fmt", str, description="csv or pdf", default="csv")],
        responses={200: None},
        summary="Export damage reports as CSV or PDF (admin only)",
    )
    @action(detail=False, methods=["get"], url_path="export", url_name="export")
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv").lower()
        qs = DamageReport.objects.select_related(
            "equipment_return__booking", "booking_item__equipment"
        ).all()
        rows = [
            {
                "ID": str(dr.id),
                "Booking Ref": dr.equipment_return.booking.booking_reference
                    if dr.equipment_return and dr.equipment_return.booking else "",
                "Equipment": dr.booking_item.equipment.equipment_name
                    if dr.booking_item and dr.booking_item.equipment else "",
                "Severity": dr.severity,
                "Qty Damaged": dr.quantity_damaged,
                "Repair Cost": str(dr.repair_cost) if dr.repair_cost else "",
                "Amount Paid": str(dr.amount_paid) if dr.amount_paid else "",
                "Resolution Status": dr.resolution_status,
                "Created At": dr.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for dr in qs
        ]
        if fmt == "pdf":
            return export_pdf("Damage Reports", self._EXPORT_HEADERS, rows, "damage_reports")
        return export_csv(self._EXPORT_HEADERS, rows, "damage_reports")
