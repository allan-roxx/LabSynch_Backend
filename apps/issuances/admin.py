from django.contrib import admin

from .models import EquipmentIssuance, EquipmentReturn


@admin.register(EquipmentIssuance)
class EquipmentIssuanceAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "issued_by",
        "received_by",
        "issued_at",
    )
    list_filter = ("issued_at",)
    search_fields = (
        "booking__booking_reference",
        "issued_by__email",
        "received_by__email",
    )
    readonly_fields = ("created_at", "updated_at", "issued_at")


@admin.register(EquipmentReturn)
class EquipmentReturnAdmin(admin.ModelAdmin):
    list_display = (
        "booking",
        "received_by",
        "returned_by",
        "has_damage",
        "returned_at",
    )
    list_filter = ("has_damage", "returned_at")
    search_fields = (
        "booking__booking_reference",
        "received_by__email",
        "returned_by__email",
    )
    readonly_fields = ("created_at", "updated_at", "returned_at")
