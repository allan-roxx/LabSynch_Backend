"""
Views for Reports app — admin-only analytics endpoints.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.permissions import IsAdminUser
from common.utils import success_response
from .serializers import DateRangeSerializer
from .services import (
    get_booking_report,
    get_client_report,
    get_dashboard_metrics,
    get_equipment_report,
    get_financial_report,
)


class DashboardMetricsView(APIView):
    """GET /api/reports/dashboard/ — top-level KPIs."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: inline_serializer("DashboardMetrics", fields={
            "total_bookings": drf_serializers.IntegerField(),
            "active_bookings": drf_serializers.IntegerField(),
            "overdue_bookings": drf_serializers.IntegerField(),
            "revenue_total": drf_serializers.CharField(),
            "revenue_this_month": drf_serializers.CharField(),
            "total_schools": drf_serializers.IntegerField(),
            "total_equipment": drf_serializers.IntegerField(),
            "pending_damage_reports": drf_serializers.IntegerField(),
            "today_pickups": drf_serializers.IntegerField(),
            "today_returns": drf_serializers.IntegerField(),
            "today_pending_payment": drf_serializers.IntegerField(),
        })},
        summary="Admin dashboard KPIs",
    )
    def get(self, request):
        data = get_dashboard_metrics()
        return success_response(data=data, message="Dashboard metrics retrieved successfully.")


class BookingReportView(APIView):
    """GET /api/reports/bookings/?start_date=...&end_date=..."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        parameters=[DateRangeSerializer],
        responses={200: inline_serializer("BookingReport", fields={
            "total": drf_serializers.IntegerField(),
            "by_status": drf_serializers.DictField(child=drf_serializers.IntegerField()),
            "average_duration_days": drf_serializers.IntegerField(allow_null=True),
        })},
        summary="Booking analytics with optional date range",
    )
    def get(self, request):
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = get_booking_report(
            start_date=serializer.validated_data.get("start_date"),
            end_date=serializer.validated_data.get("end_date"),
        )
        return success_response(data=data, message="Booking report retrieved successfully.")


class FinancialReportView(APIView):
    """GET /api/reports/financial/?start_date=...&end_date=..."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        parameters=[DateRangeSerializer],
        responses={200: inline_serializer("FinancialReport", fields={
            "total_revenue": drf_serializers.CharField(),
            "payment_count": drf_serializers.IntegerField(),
            "outstanding_damage_cost": drf_serializers.CharField(),
        })},
        summary="Financial / revenue report with optional date range",
    )
    def get(self, request):
        serializer = DateRangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = get_financial_report(
            start_date=serializer.validated_data.get("start_date"),
            end_date=serializer.validated_data.get("end_date"),
        )
        return success_response(data=data, message="Financial report retrieved successfully.")


class EquipmentReportView(APIView):
    """GET /api/reports/equipment/ — per-equipment utilisation."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: inline_serializer("EquipmentReportItem", fields={
            "equipment_id": drf_serializers.UUIDField(),
            "equipment_name": drf_serializers.CharField(),
            "equipment_code": drf_serializers.CharField(),
            "times_booked": drf_serializers.IntegerField(),
            "total_quantity_booked": drf_serializers.IntegerField(),
            "total_revenue": drf_serializers.DecimalField(max_digits=12, decimal_places=2),
        }, many=True)},
        summary="Equipment utilisation report",
    )
    def get(self, request):
        data = get_equipment_report()
        return success_response(data=data, message="Equipment report retrieved successfully.")


class ClientReportView(APIView):
    """GET /api/reports/clients/ — per-school activity summary."""

    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        responses={200: inline_serializer("ClientReportItem", fields={
            "id": drf_serializers.UUIDField(),
            "school_name": drf_serializers.CharField(),
            "county": drf_serializers.CharField(),
            "liability_status": drf_serializers.CharField(),
            "booking_count": drf_serializers.IntegerField(),
            "total_spend": drf_serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True),
        }, many=True)},
        summary="Client activity report",
    )
    def get(self, request):
        data = get_client_report()
        return success_response(data=data, message="Client report retrieved successfully.")
