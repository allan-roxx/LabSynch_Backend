from django.contrib import admin

from .models import Booking, BookingItem


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "school_profile",
        "pickup_date",
        "return_date",
        "status",
        "requires_transport",
        "transport_cost",
        "total_amount",
        "overdue_penalty",
        "penalty_carried_forward",
        "penalty_cleared",
        "created_at",
    )
    list_filter = ("status", "requires_transport", "penalty_cleared", "pickup_date", "return_date")
    search_fields = (
        "booking_reference",
        "school_profile__school_name",
        "school_profile__user__email",
    )
    ordering = ("-created_at",)
    # Penalty fields are owned by the service layer — never allow admin to overwrite them.
    readonly_fields = (
        "booking_reference",
        "total_amount",
        "transport_cost",
        "overdue_penalty",
        "penalty_carried_forward",
        "penalty_cleared",
        "created_at",
        "updated_at",
    )
    inlines = [BookingItemInline]
