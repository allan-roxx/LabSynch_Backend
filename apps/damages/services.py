"""
Services for Damage Reports.
"""

from django.db import transaction

from apps.bookings.models import BookingItem
from apps.issuances.models import EquipmentReturn
from rest_framework.exceptions import ValidationError
from .models import DamageReport, ResolutionStatus


@transaction.atomic
def create_damage_report(
    equipment_return: EquipmentReturn,
    booking_item: BookingItem,
    reported_by,
    quantity_damaged: int,
    severity: str,
    description: str,
    photo_urls: list = None
) -> DamageReport:
    """
    Creates a formal damage report linking an executed return to a specific line item.
    """
    if booking_item.booking != equipment_return.booking:
        raise ValidationError({"booking_item": "This item does not belong to the returned booking."})
        
    if quantity_damaged > booking_item.quantity:
        raise ValidationError({"quantity_damaged": "Cannot report more damaged items than were initially booked."})
        
    report = DamageReport.objects.create(
        equipment_return=equipment_return,
        booking_item=booking_item,
        reported_by=reported_by,
        quantity_damaged=quantity_damaged,
        severity=severity,
        description=description,
        photo_urls=photo_urls or []
    )
    
    return report


@transaction.atomic
def resolve_damage_report(
    damage_report: DamageReport,
    resolution_status: str,
    repair_cost=None
) -> DamageReport:
    """
    Updates the damage report resolution (e.g. charging the school or waiving).
    """
    if resolution_status not in [choice[0] for choice in ResolutionStatus.choices]:
        raise ValidationError({"resolution_status": "Invalid resolution status."})
        
    damage_report.resolution_status = resolution_status
    if repair_cost is not None:
        damage_report.repair_cost = repair_cost
        
    damage_report.save(update_fields=["resolution_status", "repair_cost", "updated_at"])
    return damage_report
