"""
Services for Maintenance Schedules.
"""

from django.db import transaction
from django.utils import timezone

from apps.equipment.models import Equipment
from rest_framework.exceptions import ValidationError
from .models import MaintenanceSchedule, MaintenanceStatus
from apps.audit.services import log_action
from apps.audit.models import AuditLog


@transaction.atomic
def create_maintenance_schedule(
    equipment: Equipment,
    maintenance_type: str,
    description: str,
    scheduled_date,
    notes: str = ""
) -> MaintenanceSchedule:
    """
    Creates a new maintenance schedule.
    """
    schedule = MaintenanceSchedule.objects.create(
        equipment=equipment,
        maintenance_type=maintenance_type,
        description=description,
        scheduled_date=scheduled_date,
        notes=notes
    )

    log_action(
        action=AuditLog.Action.CREATE,
        instance=schedule,
        changes={"equipment": str(equipment.id), "maintenance_type": maintenance_type, "scheduled_date": str(scheduled_date)},
    )

    return schedule


@transaction.atomic
def update_maintenance_status(
    schedule: MaintenanceSchedule,
    status: str,
    technician_name: str = "",
    cost=None,
    notes: str = ""
) -> MaintenanceSchedule:
    """
    Updates the maintenance log. If marked IN_PROGRESS, ideally it represents active work.
    If marked COMPLETED, it finishes the log.
    Since we don't have a rigid inventory lock rule defined for maintenance, this acts as a formal log.
    """
    if status not in [choice[0] for choice in MaintenanceStatus.choices]:
        raise ValidationError({"status": "Invalid maintenance status."})
        
    schedule.status = status
    if status == MaintenanceStatus.COMPLETED and not schedule.completed_date:
        schedule.completed_date = timezone.now().date()
        
    if technician_name:
        schedule.technician_name = technician_name
    if cost is not None:
        schedule.cost = cost
    if notes:
        schedule.notes = notes
        
    schedule.save(
        update_fields=[
            "status", "completed_date", "technician_name", "cost", "notes", "updated_at"
        ]
    )

    log_action(
        action=AuditLog.Action.UPDATE,
        instance=schedule,
        changes={"status": status, "technician_name": technician_name, "cost": str(cost) if cost else None},
    )

    return schedule
