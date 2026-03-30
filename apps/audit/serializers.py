"""
Serializers for the Audit app (read-only).
"""

from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)
    model_name = serializers.CharField(source="content_type.model", read_only=True, default=None)
    app_label = serializers.CharField(source="content_type.app_label", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "action",
            "app_label",
            "model_name",
            "object_id",
            "object_repr",
            "changes",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
