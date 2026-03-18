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
