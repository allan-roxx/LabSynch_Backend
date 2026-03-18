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
    WAIVED = "WAIVED", "Waived/Forgiven"
    RESOLVED = "RESOLVED", "Resolved and Closed"


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
        null=True
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
