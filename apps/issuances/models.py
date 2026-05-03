from django.db import models

from apps.bookings.models import Booking
from apps.users.models import User
from common.models import BaseModel


class DeliveryStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Delivery"
    ON_TIME = "ON_TIME", "Delivered On Time"
    LATE = "LATE", "Delivered Late"
    FAILED = "FAILED", "Delivery Failed"


class EquipmentIssuance(BaseModel):
    """
    Records equipment handover from Labsych Admin to a School user.
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="issuance"
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="issued_equipments",
        help_text="ADMIN who handed over the equipment."
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="received_issuances",
        help_text="SCHOOL user who collected."
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    issue_notes = models.TextField(blank=True, default="")
    issue_photo_url = models.URLField(max_length=500, blank=True, default="")
    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        help_text="Outcome of the physical delivery/handover.",
    )
    delivery_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes on late or failed delivery — reason, follow-up action, etc.",
    )

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "Equipment Issuance"
        verbose_name_plural = "Equipment Issuances"

    def __str__(self):
        return f"Issuance for {self.booking.booking_reference}"


class EquipmentReturn(BaseModel):
    """
    Records equipment return from a School user back to Labsych Admin.
    """
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="equipment_return"
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="received_returns",
        help_text="ADMIN who received the equipment back."
    )
    returned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="returned_equipments",
        help_text="SCHOOL user who returned the equipment."
    )
    returned_at = models.DateTimeField(auto_now_add=True)
    return_notes = models.TextField(blank=True, default="")
    return_photo_url = models.URLField(max_length=500, blank=True, default="")
    has_damage = models.BooleanField(default=False)

    class Meta:
        ordering = ["-returned_at"]
        verbose_name = "Equipment Return"
        verbose_name_plural = "Equipment Returns"

    def __str__(self):
        return f"Return for {self.booking.booking_reference}"
