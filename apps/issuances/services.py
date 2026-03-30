"""
Business logic for Equipment Issuances and Returns.
"""

from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus
from apps.equipment.models import Equipment
from rest_framework.exceptions import ValidationError
from .models import EquipmentIssuance, EquipmentReturn
from apps.audit.services import log_action
from apps.audit.models import AuditLog


@transaction.atomic
def issue_equipment(
    booking: Booking,
    issued_by,
    received_by,
    issue_notes: str = "",
    issue_photo_url: str = ""
) -> EquipmentIssuance:
    """
    Hands over equipment to the school user.
    Only PAID bookings can be issued.
    """
    if booking.status != BookingStatus.PAID:
        raise ValidationError({"booking": f"Cannot issue equipment. Booking is in {booking.status} state, requires PAID."})
        
    if hasattr(booking, 'issuance'):
        raise ValidationError({"booking": "Equipment already issued for this booking."})
        
    issuance = EquipmentIssuance.objects.create(
        booking=booking,
        issued_by=issued_by,
        received_by=received_by,
        issue_notes=issue_notes,
        issue_photo_url=issue_photo_url,
    )
    
    booking.status = BookingStatus.ISSUED
    booking.save(update_fields=["status", "updated_at"])

    log_action(
        action=AuditLog.Action.ISSUE,
        instance=issuance,
        actor=issued_by,
        changes={"booking": str(booking.id), "status": BookingStatus.ISSUED},
    )

    return issuance


@transaction.atomic
def return_equipment(
    booking: Booking,
    received_by,
    returned_by,
    return_notes: str = "",
    return_photo_url: str = "",
    has_damage: bool = False
) -> EquipmentReturn:
    """
    Receives equipment back from the school user.
    Restores equipment availability based on the booking items.
    """
    if booking.status != BookingStatus.ISSUED and booking.status != BookingStatus.OVERDUE:
        raise ValidationError({"booking": f"Cannot return equipment. Booking is in {booking.status} state, requires ISSUED or OVERDUE."})
        
    if hasattr(booking, 'equipment_return'):
        raise ValidationError({"booking": "Equipment already returned for this booking."})
        
    return_record = EquipmentReturn.objects.create(
        booking=booking,
        received_by=received_by,
        returned_by=returned_by,
        return_notes=return_notes,
        return_photo_url=return_photo_url,
        has_damage=has_damage,
    )
    
    booking.status = BookingStatus.COMPLETED
    booking.save(update_fields=["status", "updated_at"])

    log_action(
        action=AuditLog.Action.RETURN,
        instance=return_record,
        actor=received_by,
        changes={"booking": str(booking.id), "has_damage": has_damage, "status": BookingStatus.COMPLETED},
    )

    # Restore quantity to available pool
    equipment_ids = [str(item.equipment_id) for item in booking.booking_items.all()]
    equipment_ids.sort()  # Prevents deadlocks
    
    equipments = Equipment.objects.select_for_update().filter(id__in=equipment_ids)
    eq_map = {str(eq.id): eq for eq in equipments}

    for item in booking.booking_items.all():
        eq = eq_map.get(str(item.equipment_id))
        if eq:
            eq.available_quantity += item.quantity
            eq.save(update_fields=["available_quantity", "updated_at"])
            
    return return_record
