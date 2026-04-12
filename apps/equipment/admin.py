from django.contrib import admin

from .models import Equipment, EquipmentCategory, EquipmentImage, PricingRule, TransportZone


@admin.register(TransportZone)
class TransportZoneAdmin(admin.ModelAdmin):
    list_display = ("zone_name", "base_transport_fee", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("zone_name",)
    ordering = ("zone_name",)


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ("category_name", "display_order", "created_at")
    search_fields = ("category_name",)
    ordering = ("display_order", "category_name")


class EquipmentImageInline(admin.TabularInline):
    model = EquipmentImage
    extra = 1


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        "equipment_name",
        "equipment_code",
        "category",
        "total_quantity",
        "available_quantity",
        "unit_price_per_day",
        "condition",
        "is_active",
        "requires_personnel",
    )
    list_filter = ("category", "condition", "is_active", "requires_personnel")
    search_fields = ("equipment_name", "equipment_code")
    ordering = ("category__display_order", "equipment_name")
    inlines = [EquipmentImageInline]
    readonly_fields = ("created_at", "updated_at")


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "discount_percentage",
        "min_days",
        "max_days",
        "effective_from",
        "effective_to",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("category__category_name",)
    ordering = ("category", "min_days")
