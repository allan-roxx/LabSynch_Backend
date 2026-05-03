"""
Notification services.

Email delivery is handled by Celery tasks in tasks.py.
This module handles creating and managing in-app Notification records.
"""

import logging
from uuid import UUID

from apps.users.models import User
from .models import Notification, NotificationType

logger = logging.getLogger(__name__)


def create_notification(
    user: User,
    notification_type: str,
    title: str,
    body: str,
    *,
    booking_id: UUID | None = None,
    payment_id: UUID | None = None,
    issuance_id: UUID | None = None,
) -> Notification:
    """
    Persist a single in-app notification for a user.
    Silently logs on failure so a notification bug never breaks the calling task.
    """
    try:
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            booking_id=booking_id,
            payment_id=payment_id,
            issuance_id=issuance_id,
        )
    except Exception as exc:
        logger.error(
            "Failed to create in-app notification for user %s: %s",
            user.id, str(exc), exc_info=True,
        )
        return None


def mark_notification_read(notification_id: str, user: User) -> Notification:
    """Mark a single notification as read. Raises DoesNotExist if not owned by user."""
    notification = Notification.objects.get(id=notification_id, user=user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
    return notification


def mark_all_read(user: User) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def get_unread_count(user: User) -> int:
    """Return the number of unread notifications for a user."""
    return Notification.objects.filter(user=user, is_read=False).count()
