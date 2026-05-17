from django.db import models

from apps.bookings.models import BookingItem
from apps.issuances.models import EquipmentReturn
from apps.users.models import User
from common.models import BaseModel


class DamageSeverity(models.TextChoices):
    MINOR = "MINOR", "Minor"
    MODERATE = "MODERATE", "Moderate"
    SEVERE = "SEVERE", "Severe"


class ResolutionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Assessment"
    CHARGED = "CHARGED", "Charged to School"
    PAID = "PAID", "Paid by School"
    WAIVED = "WAIVED", "Waived/Forgiven"
    RESOLVED = "RESOLVED", "Resolved and Closed"


class DamagePaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class DamageReport(BaseModel):
    """
    Log of equipment damage reported upon return.
    Affects school account standing/billing.
    """
    equipment_return = models.ForeignKey(
        EquipmentReturn,
        on_delete=models.CASCADE,
        related_name="damage_reports"
    )
    booking_item = models.ForeignKey(
        BookingItem,
        on_delete=models.CASCADE,
        related_name="damage_reports"
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="ADMIN who reported the damage."
    )
    
    quantity_damaged = models.PositiveIntegerField(default=1)
    severity = models.CharField(
        max_length=20,
        choices=DamageSeverity.choices,
        default=DamageSeverity.MINOR
    )
    description = models.TextField()
    photo_urls = models.JSONField(default=list, blank=True)
    
    repair_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Assessed repair/replacement cost.",
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Amount the school has paid toward this damage.",
    )
    resolution_status = models.CharField(
        max_length=20,
        choices=ResolutionStatus.choices,
        default=ResolutionStatus.PENDING
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Damage Report"
        verbose_name_plural = "Damage Reports"

    def __str__(self):
        return f"Damage ({self.severity}) on {self.booking_item.equipment.equipment_name}"

    @property
    def amount_outstanding(self):
        """Remaining balance owed by the school for this damage."""
        if self.repair_cost is None:
            return 0
        return max(self.repair_cost - self.amount_paid, 0)


class DamageSettlementPayment(BaseModel):
    """
    M-Pesa settlement attempts for damage liabilities.
    Updated asynchronously by the Daraja callback.
    """

    transaction_ref = models.CharField(max_length=50, unique=True, db_index=True)
    damage_report = models.ForeignKey(
        DamageReport,
        on_delete=models.PROTECT,
        related_name="settlement_payments",
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    mpesa_phone_number = models.CharField(max_length=20, blank=True, null=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    mpesa_checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payment_status = models.CharField(
        max_length=20,
        choices=DamagePaymentStatus.choices,
        default=DamagePaymentStatus.PENDING,
    )
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    callback_response = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-initiated_at"]
        verbose_name = "Damage Settlement Payment"
        verbose_name_plural = "Damage Settlement Payments"

    def __str__(self):
        return f"{self.transaction_ref} for damage {self.damage_report_id}"
