"""
Serializers for Payments module.
"""

from rest_framework import serializers

from .models import Payment


class PaymentReadSerializer(serializers.ModelSerializer):
    """Returns payment record representation."""
    booking_reference = serializers.CharField(source="booking.booking_reference", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "transaction_ref",
            "booking_reference",
            "amount_paid",
            "payment_method",
            "payment_status",
            "mpesa_transaction_id",
            "mpesa_phone_number",
            "initiated_at",
            "completed_at",
        ]


class STKPushRequestSerializer(serializers.Serializer):
    """Validates the initiation M-Pesa request payload."""
    booking_id = serializers.UUIDField()
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        # Allow numbers starting with 0, 254, or +254
        stripped = value.replace(" ", "").replace("-", "")
        if not (stripped.startswith("07") or stripped.startswith("01") or 
                stripped.startswith("2547") or stripped.startswith("2541") or
                stripped.startswith("+2547") or stripped.startswith("+2541")):
            raise serializers.ValidationError("Valid Kenyan mobile number is required (Safaricom M-Pesa).")
        return stripped
