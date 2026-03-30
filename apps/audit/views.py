"""
Views for the Audit app.
All endpoints are restricted to ADMIN users.
"""

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from common.pagination import StandardResultsPagination
from common.permissions import IsAdminUser
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only endpoint for browsing the audit log.
    Restricted to ADMIN users only.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return AuditLog.objects.select_related("actor", "content_type").all()
