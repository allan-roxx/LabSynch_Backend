"""
Business logic for Equipment Issuances (dispatch) and Returns.
"""

from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatus, BOOKING_STATE_MACHINE
from apps.equipment.models import Equipment
from rest_framework.exceptions import ValidationError
from .models import EquipmentIssuance, EquipmentReturn
from apps.audit.services import log_action
from apps.audit.models import AuditLog


def _validate_transition(booking: Booking, target_status: str):
    """Raise ValidationError if the transition is not allowed."""
    allowed = BOOKING_STATE_MACHINE.get(booking.status, set())
    if target_status not in allowed:
        raise ValidationError(
            {"booking": f"Cannot transition from {booking.status} to {target_status}."}
        )


@transaction.atomic
def issue_equipment(
    booking: Booking,
    issued_by,
    received_by,
    issue_notes: str = "",
    issue_photo_url: str = ""
) -> EquipmentIssuance:
    """
    Hands over / dispatches equipment to the school user.
    RESERVED bookings transition to DISPATCHED (transport) or IN_USE (pickup).
    DISPATCHED bookings transition to IN_USE (delivery confirmed).
    """
    if booking.status == BookingStatus.RESERVED:
        target = BookingStatus.DISPATCHED if booking.requires_transport else BookingStatus.IN_USE
    elif booking.status == BookingStatus.DISPATCHED:
        target = BookingStatus.IN_USE
    else:
        raise ValidationError(
            {"booking": f"Cannot issue equipment. Booking is in {booking.status} state, requires RESERVED or DISPATCHED."}
        )

    _validate_transition(booking, target)

    if hasattr(booking, 'issuance') and target == BookingStatus.IN_USE and booking.status == BookingStatus.DISPATCHED:
        # Dispatch already recorded — just update status to IN_USE
        booking.status = target
        booking.save(update_fields=["status", "updated_at"])

        log_action(
            action=AuditLog.Action.ISSUE,
            instance=booking,
            actor=issued_by,
            changes={"status": [BookingStatus.DISPATCHED, BookingStatus.IN_USE]},
        )
        return booking.issuance

    if hasattr(booking, 'issuance'):
        raise ValidationError({"booking": "Equipment already issued for this booking."})

    issuance = EquipmentIssuance.objects.create(
        booking=booking,
        issued_by=issued_by,
        received_by=received_by,
        issue_notes=issue_notes,
        issue_photo_url=issue_photo_url,
    )

    booking.status = target
    booking.save(update_fields=["status", "updated_at"])

    log_action(
        action=AuditLog.Action.DISPATCH if target == BookingStatus.DISPATCHED else AuditLog.Action.ISSUE,
        instance=issuance,
        actor=issued_by,
        changes={"booking": str(booking.id), "status": target},
    )

    from apps.notifications.tasks import send_equipment_issued_notification
    send_equipment_issued_notification.delay(str(issuance.id))

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
    IN_USE or OVERDUE → RETURNED.
    """
    if booking.status not in [BookingStatus.IN_USE, BookingStatus.OVERDUE]:
        raise ValidationError(
            {"booking": f"Cannot return equipment. Booking is in {booking.status} state, requires IN_USE or OVERDUE."}
        )

    _validate_transition(booking, BookingStatus.RETURNED)

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

    booking.status = BookingStatus.RETURNED
    booking.save(update_fields=["status", "updated_at"])

    log_action(
        action=AuditLog.Action.RETURN,
        instance=return_record,
        actor=received_by,
        changes={"booking": str(booking.id), "has_damage": has_damage, "status": BookingStatus.RETURNED},
    )

    # Restore quantity to available pool
    equipment_ids = [str(item.equipment_id) for item in booking.booking_items.all()]
    equipment_ids.sort()

    equipments = Equipment.objects.select_for_update().filter(id__in=equipment_ids)
    eq_map = {str(eq.id): eq for eq in equipments}

    for item in booking.booking_items.all():
        eq = eq_map.get(str(item.equipment_id))
        if eq:
            eq.available_quantity += item.quantity
            eq.save(update_fields=["available_quantity", "updated_at"])

    return return_record
