from django.db import models

from apps.equipment.models import Equipment
from common.models import BaseModel


class MaintenanceType(models.TextChoices):
    ROUTINE = "ROUTINE", "Routine Checkup"
    REPAIR = "REPAIR", "Repair"
    CALIBRATION = "CALIBRATION", "Calibration"


class MaintenanceStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class MaintenanceSchedule(BaseModel):
    """
    Tracks maintenance logs for a specific equipment catalog pool to ensure safety.
    """
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="maintenance_logs"
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
        default=MaintenanceType.ROUTINE
    )
    description = models.TextField()
    
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=MaintenanceStatus.choices,
        default=MaintenanceStatus.SCHEDULED
    )
    technician_name = models.CharField(max_length=255, blank=True, default="")
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-scheduled_date"]
        verbose_name = "Maintenance Schedule"
        verbose_name_plural = "Maintenance Schedules"

    def __str__(self):
        return f"{self.maintenance_type} for {self.equipment.equipment_name} on {self.scheduled_date}"
