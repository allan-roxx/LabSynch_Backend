"""
Custom DRF exception handler that wraps all error responses
in the standard LabSynch envelope format.

Envelope format (error):
{
    "success": false,
    "message": "...",
    "errors": { ... }
}

Registered in settings via REST_FRAMEWORK["EXCEPTION_HANDLER"].
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wrap all DRF error responses in the standard envelope.

    Also handles Django's ValidationError (raised from the service layer)
    by converting it into a DRF ValidationError first.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        # Determine a human-readable message
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            message = "Authentication credentials were not provided or are invalid."
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            message = "You do not have permission to perform this action."
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            message = "The requested resource was not found."
        elif response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            message = "Method not allowed."
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            message = "Too many requests. Please try again later."
        elif response.status_code >= 500:
            message = "An internal server error occurred."
        else:
            message = "Validation failed."

        # Build the error payload
        errors = response.data

        response.data = {
            "success": False,
            "message": message,
            "errors": errors,
        }

    return response
