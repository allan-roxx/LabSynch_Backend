from django.contrib import admin

from .models import DamageReport


@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = (
        "equipment_return",
        "booking_item",
        "severity",
        "resolution_status",
        "repair_cost",
        "created_at",
    )
    list_filter = ("severity", "resolution_status", "created_at")
    search_fields = (
        "equipment_return__booking__booking_reference",
        "booking_item__equipment__equipment_name",
    )
    readonly_fields = ("created_at", "updated_at")
