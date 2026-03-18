from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EquipmentIssuanceViewSet, EquipmentReturnViewSet

router = DefaultRouter()
router.register(r"issuances", EquipmentIssuanceViewSet, basename="issuance")
router.register(r"returns", EquipmentReturnViewSet, basename="return")

urlpatterns = [
    path("", include(router.urls)),
]
