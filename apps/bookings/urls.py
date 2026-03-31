from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, CartCheckoutView, CartItemDetailView, CartItemView, CartView

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    # Cart endpoints
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/checkout/", CartCheckoutView.as_view(), name="cart-checkout"),
    path("cart/items/", CartItemView.as_view(), name="cart-items"),
    path("cart/items/<uuid:item_id>/", CartItemDetailView.as_view(), name="cart-item-detail"),
]
