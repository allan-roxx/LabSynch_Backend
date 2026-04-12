from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models

from common.models import BaseModel


class AuditLog(BaseModel):
    """
    Immutable record of a significant action performed by a user.
    Created by the service layer; never mutated after creation.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        CANCEL = "CANCEL", "Cancel"
        APPROVE = "APPROVE", "Approve"
        DISPATCH = "DISPATCH", "Dispatch"
        ISSUE = "ISSUE", "Issue"
        RETURN = "RETURN", "Return"
        COMPLETE = "COMPLETE", "Complete"
        PAYMENT = "PAYMENT", "Payment"
        RESOLVE = "RESOLVE", "Resolve"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        help_text="User who performed the action. Null for system-triggered actions.",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    # Generic reference to any model
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary key (UUID) of the affected record.",
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable string representation of the affected record at the time of the action.",
    )
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="Dict describing what changed. Keys are field names; values are [old, new] pairs.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
