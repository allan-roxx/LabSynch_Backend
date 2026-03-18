from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MPesaCallbackView, PaymentViewSet

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    # The callback goes before the router to prevent shadowing
    path("payments/mpesa-callback/", MPesaCallbackView.as_view(), name="mpesa-callback"),
    path("", include(router.urls)),
]
