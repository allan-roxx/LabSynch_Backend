from django.db import models

from apps.users.models import User
from common.models import BaseModel


class NotificationType(models.TextChoices):
    BOOKING_CREATED = "BOOKING_CREATED", "Booking Created"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED", "Payment Received"
    EQUIPMENT_ISSUED = "EQUIPMENT_ISSUED", "Equipment Issued"
    EQUIPMENT_RETURNED = "EQUIPMENT_RETURNED", "Equipment Returned"
    EQUIPMENT_OVERDUE = "EQUIPMENT_OVERDUE", "Equipment Overdue"
    BOOKING_CANCELLED = "BOOKING_CANCELLED", "Booking Cancelled"
    PENALTY_CLEARED = "PENALTY_CLEARED", "Penalty Cleared"
    GENERAL = "GENERAL", "General"


class Notification(BaseModel):
    """
    In-app notification record for a user.
    Created alongside each outbound email so the frontend can display
    a notification bell / feed without polling email.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)

    # Optional FK links to related records (all nullable)
    booking_id = models.UUIDField(null=True, blank=True, db_index=True)
    payment_id = models.UUIDField(null=True, blank=True, db_index=True)
    issuance_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.email}"
