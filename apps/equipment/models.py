from django.db import models
from django.db.models import F, Q

from common.models import BaseModel


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
