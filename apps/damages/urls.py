from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DamageMPesaCallbackView, DamageReportViewSet

router = DefaultRouter()
router.register(r"damages", DamageReportViewSet, basename="damage")

urlpatterns = [
    path("damages/mpesa-callback/", DamageMPesaCallbackView.as_view(), name="damage-mpesa-callback"),
    path("", include(router.urls)),
]
