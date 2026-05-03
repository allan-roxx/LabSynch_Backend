"""
Views for Notifications app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminUser
from common.utils import success_response
from .models import Notification
from .serializers import NotificationSerializer
from .services import get_unread_count, mark_all_read, mark_notification_read


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/notifications/          — list my notifications (paginated)
    GET  /api/notifications/{id}/     — retrieve a single notification
    POST /api/notifications/{id}/read/ — mark one as read
    POST /api/notifications/read-all/  — mark all as read
    GET  /api/notifications/unread-count/ — number of unread notifications

    SCHOOL users see only their own. ADMIN users see all.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ("notification_type", "is_read")
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        if self.request.user.user_type == "ADMIN":
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Notifications retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Auto-mark as read on open
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=["is_read", "updated_at"])
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Notification retrieved.")

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        updated = mark_notification_read(str(notification.id), request.user)
        return success_response(
            data=NotificationSerializer(updated).data,
            message="Notification marked as read.",
        )

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all_read_action(self, request):
        """Mark all of the current user's notifications as read."""
        count = mark_all_read(request.user)
        return success_response(
            data={"updated": count},
            message=f"{count} notification(s) marked as read.",
        )

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Return the count of unread notifications for the current user."""
        count = get_unread_count(request.user)
        return success_response(
            data={"unread_count": count},
            message="Unread count retrieved.",
        )
