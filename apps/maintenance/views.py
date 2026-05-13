"""
Views for Maintenance app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter

from common.exports import export_csv, export_pdf
from common.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from common.utils import success_response
from .models import MaintenanceSchedule
from .serializers import (
    MaintenanceScheduleCreateSerializer,
    MaintenanceScheduleReadSerializer,
    MaintenanceScheduleUpdateSerializer,
)
from .services import create_maintenance_schedule, update_maintenance_status


class MaintenanceScheduleViewSet(viewsets.ModelViewSet):
    """
    CRUD for Maintenance Schedules.
    Strictly restricted to ADMIN users to manage equipment health.
    """
    permission_classes = [IsAdminUser]
    queryset = MaintenanceSchedule.objects.select_related("equipment")

    def get_serializer_class(self):
        if self.action == "create":
            return MaintenanceScheduleCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return MaintenanceScheduleUpdateSerializer
        return MaintenanceScheduleReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schedule = create_maintenance_schedule(
            equipment=serializer.validated_data["equipment"],
            maintenance_type=serializer.validated_data.get("maintenance_type", "ROUTINE"),
            description=serializer.validated_data["description"],
            scheduled_date=serializer.validated_data["scheduled_date"],
            notes=serializer.validated_data.get("notes", ""),
        )

        read_serializer = MaintenanceScheduleReadSerializer(schedule)
        return success_response(
            data=read_serializer.data,
            message="Maintenance schedule created.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_schedule = update_maintenance_status(
            schedule=schedule,
            status=serializer.validated_data.get("status", schedule.status),
            technician_name=serializer.validated_data.get("technician_name", schedule.technician_name),
            cost=serializer.validated_data.get("cost", schedule.cost),
            notes=serializer.validated_data.get("notes", schedule.notes),
        )

        read_serializer = MaintenanceScheduleReadSerializer(updated_schedule)
        return success_response(
            data=read_serializer.data,
            message="Maintenance schedule updated.",
            status_code=status.HTTP_200_OK,
        )

    _EXPORT_HEADERS = [
        "ID", "Equipment", "Type", "Status", "Scheduled Date",
        "Completed Date", "Technician", "Cost",
    ]

    @extend_schema(
        parameters=[OpenApiParameter("fmt", str, description="csv or pdf", default="csv")],
        responses={200: None},
        summary="Export maintenance schedules as CSV or PDF (admin only)",
    )
    @action(detail=False, methods=["get"], url_path="export", url_name="export")
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv").lower()
        qs = MaintenanceSchedule.objects.select_related("equipment").all()
        rows = [
            {
                "ID": str(m.id),
                "Equipment": m.equipment.equipment_name if m.equipment else "",
                "Type": m.maintenance_type,
                "Status": m.status,
                "Scheduled Date": str(m.scheduled_date),
                "Completed Date": str(m.completed_date) if m.completed_date else "",
                "Technician": m.technician_name or "",
                "Cost": str(m.cost) if m.cost else "",
            }
            for m in qs
        ]
        if fmt == "pdf":
            return export_pdf("Maintenance Schedules", self._EXPORT_HEADERS, rows, "maintenance")
        return export_csv(self._EXPORT_HEADERS, rows, "maintenance")
