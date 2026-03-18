"""
Business logic for Equipment & Inventory.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Equipment, EquipmentCategory, EquipmentImage, PricingRule


@transaction.atomic
def create_equipment(**data):
    """
    Create a new equipment item.
    Initializes available_quantity to equal total_quantity.
    """
    total_quantity = data.get("total_quantity", 0)
    data["available_quantity"] = total_quantity

    equipment = Equipment(**data)
    try:
        equipment.full_clean()
        equipment.save()
    except ValidationError as e:
        raise ValidationError(e.message_dict)

    return equipment


@transaction.atomic
def update_equipment(equipment: Equipment, **data):
    """
    Update an existing equipment item.
    Adjusts available_quantity if total_quantity is modified.
    """
    if "total_quantity" in data:
        new_total = data["total_quantity"]
        diff = new_total - equipment.total_quantity
        
        # Adjust available_quantity
        new_available = equipment.available_quantity + diff
        if new_available < 0:
            raise ValidationError(
                {"total_quantity": "Cannot reduce total quantity below currently rented out items."}
            )
        data["available_quantity"] = new_available

    for key, value in data.items():
        setattr(equipment, key, value)

    try:
        equipment.full_clean()
        equipment.save()
    except ValidationError as e:
        raise ValidationError(e.message_dict)

    return equipment


def deactivate_equipment(equipment: Equipment):
    """
    Soft-delete an equipment item.
    """
    equipment.deactivate()
    return equipment
