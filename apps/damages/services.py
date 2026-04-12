"""
Services for Damage Reports.
"""

import logging

from django.db import transaction

from apps.bookings.models import BookingItem
from apps.issuances.models import EquipmentReturn
from apps.users.models import LiabilityStatus
from rest_framework.exceptions import ValidationError
from .models import DamageReport, ResolutionStatus
from apps.audit.services import log_action
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


def _update_school_liability(school_profile):
    """
    Recalculate the school's liability_status based on outstanding damage reports.
    """
    has_outstanding = DamageReport.objects.filter(
        equipment_return__booking__school_profile=school_profile,
        resolution_status__in=[ResolutionStatus.PENDING, ResolutionStatus.CHARGED],
    ).exists()

    new_status = LiabilityStatus.HAS_OUTSTANDING if has_outstanding else LiabilityStatus.CLEAR
    if school_profile.liability_status != new_status:
        school_profile.liability_status = new_status
        school_profile.save(update_fields=["liability_status", "updated_at"])
        logger.info(
            "School %s liability_status updated to %s",
            school_profile.id, new_status,
        )


@transaction.atomic
def create_damage_report(
    equipment_return: EquipmentReturn,
    booking_item: BookingItem,
    reported_by,
    quantity_damaged: int,
    severity: str,
    description: str,
    photo_urls: list = None,
    repair_cost=None,
) -> DamageReport:
    """
    Creates a formal damage report linking an executed return to a specific line item.
    Sets the school's liability_status to HAS_OUTSTANDING.
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
        photo_urls=photo_urls or [],
        repair_cost=repair_cost,
    )

    log_action(
        action=AuditLog.Action.CREATE,
        instance=report,
        actor=reported_by,
        changes={"severity": severity, "quantity_damaged": quantity_damaged},
    )

    # Update school liability
    school_profile = equipment_return.booking.school_profile
    _update_school_liability(school_profile)

    return report


@transaction.atomic
def resolve_damage_report(
    damage_report: DamageReport,
    resolution_status: str,
    repair_cost=None,
    amount_paid=None,
) -> DamageReport:
    """
    Updates the damage report resolution (e.g. charging the school or waiving).
    Recalculates school liability after resolution.
    """
    if resolution_status not in [choice[0] for choice in ResolutionStatus.choices]:
        raise ValidationError({"resolution_status": "Invalid resolution status."})
        
    damage_report.resolution_status = resolution_status
    update_fields = ["resolution_status", "updated_at"]

    if repair_cost is not None:
        damage_report.repair_cost = repair_cost
        update_fields.append("repair_cost")
    if amount_paid is not None:
        damage_report.amount_paid = amount_paid
        update_fields.append("amount_paid")

    damage_report.save(update_fields=update_fields)

    log_action(
        action=AuditLog.Action.RESOLVE,
        instance=damage_report,
        changes={
            "resolution_status": resolution_status,
            "repair_cost": str(repair_cost) if repair_cost else None,
        },
    )

    # Recalculate school liability
    school_profile = damage_report.equipment_return.booking.school_profile
    _update_school_liability(school_profile)

    return damage_report
