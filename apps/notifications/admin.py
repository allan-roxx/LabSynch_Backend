from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read")
    search_fields = ("title", "user__email", "body")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "booking_id", "payment_id", "issuance_id")
