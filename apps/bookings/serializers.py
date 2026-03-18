"""
Serializers for Booking app.
"""

from rest_framework import serializers

from apps.equipment.serializers import EquipmentReadSerializer
from .models import Booking, BookingItem


class BookingItemCreateSerializer(serializers.Serializer):
    """Validates individual items within a booking request."""
    equipment = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class BookingCreateSerializer(serializers.Serializer):
    """Validates incoming booking requests."""
    pickup_date = serializers.DateField()
    return_date = serializers.DateField()
    special_instructions = serializers.CharField(required=False, allow_blank=True, default="")
    items = BookingItemCreateSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        if attrs["return_date"] <= attrs["pickup_date"]:
            raise serializers.ValidationError({"return_date": "Return date must be after pickup date."})
        return attrs


class BookingItemReadSerializer(serializers.ModelSerializer):
    equipment = EquipmentReadSerializer(read_only=True)

    class Meta:
        model = BookingItem
        fields = ["id", "equipment", "quantity", "unit_price", "subtotal"]


class BookingReadSerializer(serializers.ModelSerializer):
    booking_items = BookingItemReadSerializer(many=True, read_only=True)
    school_name = serializers.CharField(source="school_profile.school_name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_reference",
            "school_name",
            "pickup_date",
            "return_date",
            "status",
            "total_amount",
            "special_instructions",
            "created_at",
            "booking_items",
        ]


class AvailabilityCheckSerializer(serializers.Serializer):
    """Validates the availability check request."""
    pickup_date = serializers.DateField()
    return_date = serializers.DateField()

    def validate(self, attrs):
        if attrs["return_date"] <= attrs["pickup_date"]:
            raise serializers.ValidationError({"return_date": "Return date must be after pickup date."})
        return attrs
