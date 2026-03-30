from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "model_name", "object_repr", "ip_address", "created_at")
    list_filter = ("action", "content_type")
    search_fields = ("actor__email", "object_repr", "object_id")
    readonly_fields = (
        "id",
        "actor",
        "action",
        "content_type",
        "object_id",
        "object_repr",
        "changes",
        "ip_address",
        "created_at",
        "updated_at",
    )

    def model_name(self, obj):
        return obj.content_type.model if obj.content_type else "-"

    model_name.short_description = "Model"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
