"""
URL configuration for LabSynch project.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # App URLs
    path("api/auth/", include("apps.authentication.urls")),
    path("api/", include("apps.equipment.urls")),
    path("api/", include("apps.bookings.urls")),
    path("api/", include("apps.payments.urls")),
    path("api/", include("apps.issuances.urls")),
    path("api/", include("apps.damages.urls")),
    path("api/", include("apps.maintenance.urls")),
]

from django.conf import settings
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
