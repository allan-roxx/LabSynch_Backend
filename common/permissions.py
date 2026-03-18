"""
Custom permission classes for role-based access control.
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows access only to users with user_type == 'ADMIN'.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "ADMIN"
        )


class IsSchoolUser(BasePermission):
    """
    Allows access only to users with user_type == 'SCHOOL'.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.user_type == "SCHOOL"
        )
