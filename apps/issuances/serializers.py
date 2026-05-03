"""
Serializers for Issuances app.
"""

from rest_framework import serializers
from .models import DeliveryStatus, EquipmentIssuance, EquipmentReturn


class EquipmentIssuanceReadSerializer(serializers.ModelSerializer):
    issued_by_email = serializers.EmailField(source="issued_by.email", read_only=True)
    received_by_email = serializers.EmailField(source="received_by.email", read_only=True)
    booking_reference = serializers.CharField(source="booking.booking_reference", read_only=True)

    class Meta:
        model = EquipmentIssuance
        fields = [
            "id",
            "booking",
            "booking_reference",
            "issued_by_email",
            "received_by_email",
            "issued_at",
            "issue_notes",
            "issue_photo_url",
            "delivery_status",
            "delivery_notes",
        ]


class EquipmentIssuanceCreateSerializer(serializers.ModelSerializer):
    """Admin writes only booking and received_by. issued_by is inferred."""
    class Meta:
        model = EquipmentIssuance
        fields = [
            "booking",
            "received_by",
            "issue_notes",
            "issue_photo_url",
        ]


class EquipmentIssuanceDeliverySerializer(serializers.Serializer):
    """Admin updates the delivery outcome for an existing issuance record."""
    delivery_status = serializers.ChoiceField(choices=DeliveryStatus.choices)
    delivery_notes = serializers.CharField(required=False, allow_blank=True)


class EquipmentReturnReadSerializer(serializers.ModelSerializer):
    received_by_email = serializers.EmailField(source="received_by.email", read_only=True)
    returned_by_email = serializers.EmailField(source="returned_by.email", read_only=True)
    booking_reference = serializers.CharField(source="booking.booking_reference", read_only=True)

    class Meta:
        model = EquipmentReturn
        fields = [
            "id",
            "booking",
            "booking_reference",
            "received_by_email",
            "returned_by_email",
            "returned_at",
            "return_notes",
            "return_photo_url",
            "has_damage",
        ]


class EquipmentReturnCreateSerializer(serializers.ModelSerializer):
    """Admin writes booking and returned_by. received_by is inferred."""
    class Meta:
        model = EquipmentReturn
        fields = [
            "booking",
            "returned_by",
            "return_notes",
            "return_photo_url",
            "has_damage",
        ]
