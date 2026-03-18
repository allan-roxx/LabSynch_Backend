"""
Views for Booking app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsAdminUser
from common.utils import success_response
from .models import Booking, BookingStatus
from .serializers import BookingCreateSerializer, BookingReadSerializer
from .services import cancel_booking, create_booking


class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Bookings.
    SCHOOL users can see/create/cancel their own bookings.
    ADMIN users can see all and update statuses.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
