from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_ref",
        "booking",
        "amount_paid",
        "payment_method",
        "payment_status",
        "mpesa_transaction_id",
        "initiated_at",
    )
    list_filter = ("payment_status", "payment_method", "initiated_at")
    search_fields = (
        "transaction_ref",
        "booking__booking_reference",
        "mpesa_transaction_id",
        "mpesa_phone_number",
        "mpesa_checkout_request_id",
    )
    ordering = ("-initiated_at",)
    readonly_fields = ("created_at", "updated_at", "initiated_at", "completed_at", "callback_response")
