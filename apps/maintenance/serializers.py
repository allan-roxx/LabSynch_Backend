"""
Serializers for Maintenance app.
"""

from rest_framework import serializers

from .models import MaintenanceSchedule, MaintenanceStatus, MaintenanceType


class MaintenanceScheduleReadSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source="equipment.equipment_name", read_only=True)
    equipment_code = serializers.CharField(source="equipment.equipment_code", read_only=True)

    class Meta:
        model = MaintenanceSchedule
        fields = [
            "id",
            "equipment",
            "equipment_name",
            "equipment_code",
            "maintenance_type",
            "description",
            "scheduled_date",
            "completed_date",
            "status",
            "technician_name",
            "cost",
            "notes",
            "created_at",
            "updated_at",
        ]


class MaintenanceScheduleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceSchedule
        fields = [
            "equipment",
            "maintenance_type",
            "description",
            "scheduled_date",
            "notes",
        ]


class MaintenanceScheduleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceSchedule
        fields = [
            "status",
            "technician_name",
            "cost",
            "notes",
        ]
