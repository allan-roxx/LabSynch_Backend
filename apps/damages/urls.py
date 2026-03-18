from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DamageReportViewSet

router = DefaultRouter()
router.register(r"damages", DamageReportViewSet, basename="damage")

urlpatterns = [
    path("", include(router.urls)),
]
