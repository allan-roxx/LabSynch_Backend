"""
Serializers for Damages app.
"""

from rest_framework import serializers

from .models import DamageReport, ResolutionStatus
from apps.bookings.models import BookingItem
from apps.issuances.models import EquipmentReturn


class DamageReportReadSerializer(serializers.ModelSerializer):
    reported_by_email = serializers.EmailField(source="reported_by.email", read_only=True)
    equipment_name = serializers.CharField(source="booking_item.equipment.equipment_name", read_only=True)
    booking_reference = serializers.CharField(source="equipment_return.booking.booking_reference", read_only=True)
    amount_outstanding = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True,
    )

    class Meta:
        model = DamageReport
        fields = [
            "id",
            "equipment_return",
            "booking_item",
            "booking_reference",
            "equipment_name",
            "reported_by",
            "reported_by_email",
            "quantity_damaged",
            "severity",
            "description",
            "photo_urls",
            "repair_cost",
            "amount_paid",
            "amount_outstanding",
            "resolution_status",
            "created_at",
            "updated_at",
        ]


class DamageReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageReport
        fields = [
            "equipment_return",
            "booking_item",
            "quantity_damaged",
            "severity",
            "description",
            "photo_urls",
        ]


class DamageReportResolveSerializer(serializers.Serializer):
    resolution_status = serializers.ChoiceField(choices=ResolutionStatus.choices)
    repair_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
