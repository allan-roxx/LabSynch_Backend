from decimal import Decimal

from django.db import models
from django.db.models import F, Q

from common.models import BaseModel


class TransportZone(BaseModel):
    """
    Geographic zone used for distance-based transport pricing.
    Examples: Kiambu Central, Thika, Ruiru, Limuru.
    """

    zone_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    base_transport_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Flat delivery fee (KES) for this zone.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["zone_name"]
        verbose_name = "Transport Zone"
        verbose_name_plural = "Transport Zones"

    def __str__(self):
        return f"{self.zone_name} (KES {self.base_transport_fee})"


class EquipmentCategory(BaseModel):
    """
    Equipment classification for easy browsing and pricing rules.
    """

    category_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    icon_url = models.URLField(max_length=500, blank=True, default="")
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ["display_order", "category_name"]
        verbose_name = "Equipment Category"
        verbose_name_plural = "Equipment Categories"

    def __str__(self):
        return self.category_name


class Condition(models.TextChoices):
    NEW = "NEW", "New"
    GOOD = "GOOD", "Good"
    FAIR = "FAIR", "Fair"
    NEEDS_MAINTENANCE = "NEEDS_MAINTENANCE", "Needs Maintenance"


class Equipment(BaseModel):
    """
    Individual equipment items available for rent.
    """

    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.PROTECT,
        related_name="equipments",
    )
    equipment_name = models.CharField(max_length=255)
    equipment_code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")

    total_quantity = models.PositiveIntegerField()
    available_quantity = models.PositiveIntegerField()

    unit_price_per_day = models.DecimalField(max_digits=12, decimal_places=2)
    condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        default=Condition.GOOD,
    )
    storage_location = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_consumable = models.BooleanField(
        default=False,
        help_text="Consumable items (reagents, paper) are single-use. No physical return expected.",
    )
    overdue_penalty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.50"),
        help_text="Multiplier on unit_price_per_day charged per overdue day (1.50 = 150% of daily rate).",
    )

    # Inventory enrichment
    acquisition_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original purchase price per unit.",
    )
    acquisition_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the equipment was acquired.",
    )

    # Specialized equipment handling
    requires_personnel = models.BooleanField(
        default=False,
        help_text="Whether this equipment needs a technician during use.",
    )
    personnel_cost_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Extra daily cost for technician support (KES).",
    )
    personnel_description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Description of personnel requirement, e.g. 'Certified 3D printer technician'.",
    )

    class Meta:
        ordering = ["category__display_order", "equipment_name"]
        verbose_name = "Equipment"
        verbose_name_plural = "Equipments"
        constraints = [
            models.CheckConstraint(
                condition=Q(available_quantity__lte=F("total_quantity")),
                name="available_qty_lte_total_qty",
            ),
            models.CheckConstraint(
                condition=Q(unit_price_per_day__gt=0),
                name="unit_price_gt_zero",
            ),
        ]

    def __str__(self):
        return f"{self.equipment_name} ({self.equipment_code})"

    def deactivate(self):
        """Soft delete / hide from catalog."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])


class EquipmentImage(BaseModel):
    """
    Multiple images per equipment item for better product display.
    """

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image_url = models.URLField(max_length=500)
    display_order = models.IntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "-uploaded_at"]
        verbose_name = "Equipment Image"
        verbose_name_plural = "Equipment Images"

    def __str__(self):
        return f"Image for {self.equipment.equipment_name}"


class PricingRule(BaseModel):
    """
    Dynamic pricing based on rental duration and category.
    """

    category = models.ForeignKey(
        EquipmentCategory,
        on_delete=models.CASCADE,
        related_name="pricing_rules",
    )
    min_days = models.PositiveIntegerField()
    max_days = models.PositiveIntegerField()
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "min_days"]
        verbose_name = "Pricing Rule"
        verbose_name_plural = "Pricing Rules"
        constraints = [
            models.CheckConstraint(
                condition=Q(max_days__gt=F("min_days")),
                name="max_days_gt_min_days",
            ),
            models.CheckConstraint(
                condition=Q(discount_percentage__gte=0),
                name="discount_percentage_gte_zero",
            ),
        ]

    def __str__(self):
        return f"{self.discount_percentage}% off {self.category.category_name} ({self.min_days}-{self.max_days} days)"
