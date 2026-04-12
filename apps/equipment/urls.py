from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EquipmentCategoryViewSet, EquipmentViewSet, PricingRuleViewSet, TransportZoneViewSet


router = DefaultRouter()
router.register(r"equipment-categories", EquipmentCategoryViewSet, basename="category")
router.register(r"equipment", EquipmentViewSet, basename="equipment")
router.register(r"pricing-rules", PricingRuleViewSet, basename="pricing-rule")
router.register(r"transport-zones", TransportZoneViewSet, basename="transport-zone")

urlpatterns = [
    path("", include(router.urls)),
]
