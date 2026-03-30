"""
Audit service — creates AuditLog entries from any part of the codebase.
"""

import logging

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    instance=None,
    actor=None,
    changes: dict = None,
    ip_address: str = None,
) -> AuditLog:
    """
    Record a significant system action in the audit log.

    Args:
        action:     One of AuditLog.Action choices.
        instance:   The Django model instance being acted upon (optional).
        actor:      The User performing the action (optional — None for system actions).
        changes:    Dict of changed fields: {"field": [old_value, new_value]}.
        ip_address: Client IP address extracted from the request (optional).

    Returns:
        The created AuditLog instance.
    """
    content_type = None
    object_id = ""
    object_repr = ""

    if instance is not None:
        try:
            content_type = ContentType.objects.get_for_model(instance)
            object_id = str(instance.pk)
            object_repr = str(instance)
        except Exception:
            logger.warning("AuditLog: could not resolve content type for %r", instance)

    entry = AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes,
        ip_address=ip_address,
    )
    return entry
