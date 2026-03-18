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
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "pickup_date", "return_date")
    search_fields = (
        "booking_reference",
        "school_profile__school_name",
        "school_profile__user__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [BookingItemInline]
