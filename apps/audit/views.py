"""
Views for the Audit app.
All endpoints are restricted to ADMIN users.
"""

import django_filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from common.exports import export_csv, export_pdf
from common.pagination import StandardResultsPagination
from common.permissions import IsAdminUser
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.ChoiceFilter(choices=AuditLog.Action.choices)
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = AuditLog
        fields = ["action"]


@extend_schema(tags=["audit-logs"])
class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Read-only endpoint for browsing the audit log.
    Restricted to ADMIN users only.

    Supports:
      - ?search=       full-text search on actor email, model name, object repr
      - ?action=       filter by action type (CREATE, UPDATE, DELETE, …)
      - ?created_at__gte=  ISO-8601 datetime lower bound
      - ?created_at__lte=  ISO-8601 datetime upper bound
      - ?ordering=     any field (default -created_at)
      - GET /export/?fmt=csv|pdf  — download filtered results
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ["actor__email", "content_type__model", "object_repr", "ip_address"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return AuditLog.objects.select_related("actor", "content_type").all()

    @extend_schema(
        summary="Export audit logs as CSV or PDF",
        parameters=[
            OpenApiParameter("fmt", description="csv or pdf", required=False, type=str),
        ],
    )
    @action(detail=False, methods=["get"], url_path="export", pagination_class=None)
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv").lower()
        qs = self.filter_queryset(self.get_queryset())

        headers = ["Date", "Action", "Actor", "Model", "Object", "IP Address"]
        rows = [
            {
                "Date": log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "",
                "Action": log.action,
                "Actor": log.actor.email if log.actor else "System",
                "Model": log.content_type.model if log.content_type else "",
                "Object": log.object_repr or "",
                "IP Address": log.ip_address or "",
            }
            for log in qs
        ]

        if fmt == "pdf":
            return export_pdf("Audit Logs", headers, rows, "audit_logs")
        return export_csv(headers, rows, "audit_logs")
