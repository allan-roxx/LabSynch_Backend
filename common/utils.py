"""
Shared utility functions for consistent API responses.
"""

from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="Success.", status_code=status.HTTP_200_OK):
    """
    Build a standard success response in the LabSynch envelope format.

    Envelope format (success):
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    payload = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data

    return Response(payload, status=status_code)


def error_response(message="An error occurred.", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Build a standard error response in the LabSynch envelope format.

    Envelope format (error):
    {
        "success": false,
        "message": "...",
        "errors": { ... }
    }
    """
    payload = {
        "success": False,
        "message": message,
    }
    if errors is not None:
        payload["errors"] = errors

    return Response(payload, status=status_code)
