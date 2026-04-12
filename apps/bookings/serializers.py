"""
Serializers for Booking app.
"""

from rest_framework import serializers

from apps.equipment.serializers import EquipmentReadSerializer
from .models import Booking, BookingItem, Cart, CartItem


class BookingItemCreateSerializer(serializers.Serializer):
    """Validates individual items within a booking request."""
    equipment = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class BookingCreateSerializer(serializers.Serializer):
    """Validates incoming booking requests."""
    pickup_date = serializers.DateField()
    return_date = serializers.DateField()
    special_instructions = serializers.CharField(required=False, allow_blank=True, default="")
    requires_transport = serializers.BooleanField(required=False, default=False)
    items = BookingItemCreateSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        if attrs["return_date"] <= attrs["pickup_date"]:
            raise serializers.ValidationError({"return_date": "Return date must be after pickup date."})
        return attrs


class BookingItemReadSerializer(serializers.ModelSerializer):
    equipment = EquipmentReadSerializer(read_only=True)

    class Meta:
        model = BookingItem
        fields = ["id", "equipment", "quantity", "unit_price", "subtotal", "personnel_cost"]


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
            "requires_transport",
            "transport_cost",
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


# ---------------------------------------------------------------------------
# Cart serializers
# ---------------------------------------------------------------------------

class CartItemWriteSerializer(serializers.Serializer):
    """Used for POST /api/cart/items/ — add or update an item."""

    equipment = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class CartItemUpdateSerializer(serializers.Serializer):
    """Used for PATCH /api/cart/items/<id>/ — change quantity only."""

    quantity = serializers.IntegerField(min_value=1)


class CartItemReadSerializer(serializers.ModelSerializer):
    equipment = EquipmentReadSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "equipment", "quantity", "created_at"]


class CartDatesSerializer(serializers.Serializer):
    """Used for PATCH /api/cart/ — set pickup/return dates."""

    pickup_date = serializers.DateField(required=False, allow_null=True)
    return_date = serializers.DateField(required=False, allow_null=True)
    special_instructions = serializers.CharField(required=False, allow_blank=True)
    requires_transport = serializers.BooleanField(required=False)

    def validate(self, attrs):
        pickup = attrs.get("pickup_date")
        ret = attrs.get("return_date")
        if pickup and ret and ret <= pickup:
            raise serializers.ValidationError({"return_date": "Return date must be after pickup date."})
        return attrs


class CartReadSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "pickup_date",
            "return_date",
            "special_instructions",
            "requires_transport",
            "item_count",
            "items",
            "updated_at",
        ]

    def get_item_count(self, obj) -> int:
        return obj.items.count()
