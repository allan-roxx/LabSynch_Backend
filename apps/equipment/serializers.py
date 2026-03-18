"""
Serializers for Equipment app.
"""

from rest_framework import serializers

from .models import Equipment, EquipmentCategory, EquipmentImage, PricingRule


class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = ["id", "category_name", "description", "icon_url", "display_order"]


class PricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingRule
        fields = [
            "id",
            "category",
            "min_days",
            "max_days",
            "discount_percentage",
            "effective_from",
            "effective_to",
            "is_active",
        ]


class EquipmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentImage
        fields = ["id", "image_url", "is_primary", "display_order"]


class EquipmentReadSerializer(serializers.ModelSerializer):
    category = EquipmentCategorySerializer(read_only=True)
    images = EquipmentImageSerializer(many=True, read_only=True)

    class Meta:
        model = Equipment
        fields = [
            "id",
            "category",
            "equipment_name",
            "equipment_code",
            "description",
            "total_quantity",
            "available_quantity",
            "unit_price_per_day",
            "condition",
            "storage_location",
            "is_active",
            "images",
        ]


class EquipmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = [
            "category",
            "equipment_name",
            "equipment_code",
            "description",
            "total_quantity",
            "unit_price_per_day",
            "condition",
            "storage_location",
            "is_active",
        ]

    def validate_total_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Total quantity cannot be negative.")
        return value

    def validate_unit_price_per_day(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value
