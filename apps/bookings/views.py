"""
Views for Booking app.
"""

from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.permissions import IsAdminUser, IsSchoolUser
from common.utils import error_response, success_response
from .models import Booking, BookingStatus
from .serializers import (
    BookingCreateSerializer,
    BookingReadSerializer,
    CartDatesSerializer,
    CartItemReadSerializer,
    CartItemUpdateSerializer,
    CartItemWriteSerializer,
    CartReadSerializer,
)
from .services import (
    add_or_update_cart_item,
    cancel_booking,
    checkout_cart,
    clear_cart,
    create_booking,
    get_or_create_cart,
    remove_cart_item,
    set_cart_dates,
    update_cart_item_quantity,
)


class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Bookings.
    SCHOOL users can see/create/cancel their own bookings.
    ADMIN users can see all and update statuses.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        queryset = Booking.objects.select_related("school_profile", "school_profile__user").prefetch_related(
            "booking_items", "booking_items__equipment", "booking_items__equipment__category"
        )
        if self.request.user.user_type == "ADMIN":
            return queryset
        return queryset.filter(school_profile__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingReadSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message="Bookings retrieved successfully.")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Booking details retrieved successfully.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking = create_booking(
            user=request.user,
            pickup_date=serializer.validated_data["pickup_date"],
            return_date=serializer.validated_data["return_date"],
            items_data=serializer.validated_data["items"],
            special_instructions=serializer.validated_data.get("special_instructions", ""),
        )
        
        read_serializer = BookingReadSerializer(booking)
        return success_response(
            data=read_serializer.data,
            message="Booking created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Only ADMIN users can update bookings arbitrarily."""
        if request.user.user_type != "ADMIN":
            return success_response(
                data=None, 
                message="Only administrators can update bookings.", 
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        
        # We only allow updating status directly for now, via a generic update or partial_update
        # A more robust system would have separate status transition endpoints
        if "status" in request.data:
            instance.status = request.data["status"]
            instance.save(update_fields=["status", "updated_at"])
            
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data, message="Booking updated successfully.")

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Endpoint to cancel a PENDING or CONFIRMED booking."""
        booking = self.get_object()
        cancelled_booking = cancel_booking(booking, request.user)
        
        serializer = BookingReadSerializer(cancelled_booking)
        return success_response(
            data=serializer.data,
            message="Booking cancelled successfully.",
            status_code=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Cart views  (school users only)
# ---------------------------------------------------------------------------

@extend_schema(methods=["GET"], responses={200: CartReadSerializer}, summary="Get current cart")
@extend_schema(methods=["PATCH"], request=CartDatesSerializer, responses={200: CartReadSerializer}, summary="Set cart dates / instructions")
@extend_schema(methods=["DELETE"], responses={200: OpenApiResponse(description="Cart cleared.")}, summary="Clear cart")
class CartView(APIView):
    """
    GET  /api/cart/         — retrieve the current user's cart
    PATCH /api/cart/        — set pickup_date / return_date / special_instructions
    DELETE /api/cart/       — clear all items + reset dates
    """

    permission_classes = [IsAuthenticated, IsSchoolUser]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        cart_qs = (
            type(cart).objects
            .prefetch_related("items__equipment__category", "items__equipment__images")
            .get(pk=cart.pk)
        )
        serializer = CartReadSerializer(cart_qs)
        return success_response(data=serializer.data, message="Cart retrieved successfully.")

    def patch(self, request):
        serializer = CartDatesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = set_cart_dates(
            user=request.user,
            pickup_date=serializer.validated_data.get("pickup_date"),
            return_date=serializer.validated_data.get("return_date"),
            special_instructions=serializer.validated_data.get("special_instructions"),
        )
        cart_qs = (
            type(cart).objects
            .prefetch_related("items__equipment__category", "items__equipment__images")
            .get(pk=cart.pk)
        )
        return success_response(
            data=CartReadSerializer(cart_qs).data,
            message="Cart updated successfully.",
        )

    def delete(self, request):
        clear_cart(request.user)
        return success_response(data=None, message="Cart cleared.")


@extend_schema(
    methods=["POST"],
    request=None,
    responses={201: BookingReadSerializer},
    summary="Checkout cart — creates a Booking from cart contents",
)
class CartCheckoutView(APIView):
    """
    POST /api/cart/checkout/
    Converts the cart into a Booking (status=PENDING) and clears the cart.
    """

    permission_classes = [IsAuthenticated, IsSchoolUser]

    def post(self, request):
        try:
            booking = checkout_cart(request.user)
        except ValidationError as exc:
            message = exc.message if hasattr(exc, "message") else str(exc)
            return error_response(
                message=message,
                errors={"non_field_errors": [message]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BookingReadSerializer(booking)
        return success_response(
            data=serializer.data,
            message="Booking created successfully from cart.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(
    methods=["POST"],
    request=CartItemWriteSerializer,
    responses={201: CartItemReadSerializer},
    summary="Add item to cart (or update quantity if already present)",
)
class CartItemView(APIView):
    """
    POST /api/cart/items/
    Add a new equipment item to the cart, or update its quantity if already present.
    """

    permission_classes = [IsAuthenticated, IsSchoolUser]

    def post(self, request):
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = add_or_update_cart_item(
                user=request.user,
                equipment_id=str(serializer.validated_data["equipment"]),
                quantity=serializer.validated_data["quantity"],
            )
        except ValidationError as exc:
            message = exc.message if hasattr(exc, "message") else str(exc)
            return error_response(
                message=message,
                errors={"equipment": [message]},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        from .serializers import CartItemReadSerializer
        return success_response(
            data=CartItemReadSerializer(item).data,
            message="Item added to cart.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(methods=["PATCH"], request=CartItemUpdateSerializer, responses={200: CartItemReadSerializer}, summary="Update cart item quantity")
@extend_schema(methods=["DELETE"], responses={200: OpenApiResponse(description="Item removed.")}, summary="Remove item from cart")
class CartItemDetailView(APIView):
    """
    PATCH  /api/cart/items/<item_id>/  — update quantity
    DELETE /api/cart/items/<item_id>/  — remove item
    """

    permission_classes = [IsAuthenticated, IsSchoolUser]

    def patch(self, request, item_id):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = update_cart_item_quantity(
                user=request.user,
                item_id=item_id,
                quantity=serializer.validated_data["quantity"],
            )
        except ValidationError as exc:
            message = exc.message if hasattr(exc, "message") else str(exc)
            return error_response(
                message=message,
                errors={"non_field_errors": [message]},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        from .serializers import CartItemReadSerializer
        return success_response(
            data=CartItemReadSerializer(item).data,
            message="Cart item updated.",
        )

    def delete(self, request, item_id):
        remove_cart_item(user=request.user, item_id=item_id)
        return success_response(data=None, message="Item removed from cart.")
