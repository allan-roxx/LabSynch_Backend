from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceScheduleViewSet

router = DefaultRouter()
router.register(r"maintenance", MaintenanceScheduleViewSet, basename="maintenance")

urlpatterns = [
    path("", include(router.urls)),
]
