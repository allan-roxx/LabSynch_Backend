from django.db import models
from django.db.models import CheckConstraint, Q

from apps.bookings.models import Booking
from common.models import BaseModel


class PaymentMethod(models.TextChoices):
    MPESA = "MPESA", "M-Pesa"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    CASH = "CASH", "Cash"
    CHEQUE = "CHEQUE", "Cheque"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REFUNDED = "REFUNDED", "Refunded"


class Payment(BaseModel):
    """
    Financial transaction records integrated with M-Pesa.
    """

    transaction_ref = models.CharField(max_length=50, unique=True, db_index=True)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MPESA,
    )
    
    # M-Pesa specific fields
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    mpesa_phone_number = models.CharField(max_length=20, blank=True, null=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    callback_response = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-initiated_at"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        constraints = [
            CheckConstraint(
                condition=Q(amount_paid__gt=0),
                name="payment_amount_gt_zero",
            )
        ]

    def __str__(self):
        return f"{self.transaction_ref} for {self.booking.booking_reference}"
