from django.contrib import admin

from .models import MaintenanceSchedule


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "equipment",
        "maintenance_type",
        "scheduled_date",
        "status",
        "technician_name",
    )
    list_filter = ("maintenance_type", "status", "scheduled_date")
    search_fields = (
        "equipment__equipment_name",
        "equipment__equipment_code",
        "technician_name",
    )
    readonly_fields = ("created_at", "updated_at")
