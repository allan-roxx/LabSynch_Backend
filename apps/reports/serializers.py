"""
Serializers for Reports app — lightweight date-range filter input.
"""

from rest_framework import serializers


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("end_date"):
            if attrs["end_date"] < attrs["start_date"]:
                raise serializers.ValidationError(
                    {"end_date": "End date must be on or after start date."}
                )
        return attrs
