from django.db import models
from django.db.models import F, Q

from apps.equipment.models import Equipment
from apps.users.models import SchoolProfile
from common.models import BaseModel


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    PAID = "PAID", "Paid"
    ISSUED = "ISSUED", "Issued"
    RETURNED = "RETURNED", "Returned"
    COMPLETED = "COMPLETED", "Completed"  # from ERD
    OVERDUE = "OVERDUE", "Overdue"  # from business rules
    CANCELLED = "CANCELLED", "Cancelled"


class Booking(BaseModel):
    """
    Main reservation record.
    """

    booking_reference = models.CharField(max_length=50, unique=True, db_index=True)
    school_profile = models.ForeignKey(
        SchoolProfile,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    pickup_date = models.DateField()
    return_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        constraints = [
            models.CheckConstraint(
                condition=Q(return_date__gt=F("pickup_date")),
                name="return_date_after_pickup_date",
            )
        ]

    def __str__(self):
        return f"{self.booking_reference} - {self.school_profile.school_name}"


class BookingItem(BaseModel):
    """
    Line items within a booking.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="booking_items",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="booking_items",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Booking Item"
        verbose_name_plural = "Booking Items"
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="booking_item_quantity_gt_zero",
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.equipment.equipment_name} for {self.booking.booking_reference}"
