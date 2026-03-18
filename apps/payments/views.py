"""
Views for Payments app.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from rest_framework.exceptions import ValidationError
from common.utils import success_response
from .models import Payment
from .serializers import PaymentReadSerializer, STKPushRequestSerializer
from .services import initiate_mpesa_payment, process_mpesa_callback


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Payments are read-only via standard REST. They are created via the STK push action.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentReadSerializer

    def get_queryset(self):
        queryset = Payment.objects.select_related("booking")
        if self.request.user.user_type == "ADMIN":
            return queryset
        return queryset.filter(booking__school_profile__user=self.request.user)

    @action(detail=False, methods=["post"])
    def mpesa_stk_push(self, request):
        """
        Initiates an M-Pesa STK Push to the user's phone.
        """
        serializer = STKPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        booking_id = serializer.validated_data["booking_id"]
        phone_number = serializer.validated_data["phone_number"]
        
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            raise ValidationError({"booking_id": "Booking not found."})
            
        # Ensure user owns booking (or is ADMIN)
        if booking.school_profile.user != request.user and request.user.user_type != "ADMIN":
            return success_response(
                data=None, 
                message="You do not have permission to pay for this booking.", 
                status_code=status.HTTP_403_FORBIDDEN
            )
            
        payment = initiate_mpesa_payment(booking, phone_number)
        
        return success_response(
            data={"payment_id": payment.id, "transaction_ref": payment.transaction_ref},
            message="M-Pesa payment prompt initiated successfully on your phone.",
            status_code=status.HTTP_201_CREATED,
        )


class MPesaCallbackView(APIView):
    """
    Public webhook endpoint for Safaricom Daraja API.
    Does NOT require JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # We must ALWAYS return 200 OK so Safaricom doesn't endlessly retry.
        # The service layer handles internal logging and try/except catching.
        process_mpesa_callback(request.data)
        return Response({"ResultCode": 0, "ResultDesc": "Success"})
