from django.urls import path

from .views import (
    BookingReportView,
    ClientReportView,
    DashboardMetricsView,
    EquipmentReportView,
    FinancialReportView,
    ProfitabilityReportView,
)

urlpatterns = [
    path("reports/dashboard/", DashboardMetricsView.as_view(), name="report-dashboard"),
    path("reports/bookings/", BookingReportView.as_view(), name="report-bookings"),
    path("reports/financial/", FinancialReportView.as_view(), name="report-financial"),
    path("reports/equipment/", EquipmentReportView.as_view(), name="report-equipment"),
    path("reports/clients/", ClientReportView.as_view(), name="report-clients"),
    path("reports/profitability/", ProfitabilityReportView.as_view(), name="report-profitability"),
]
