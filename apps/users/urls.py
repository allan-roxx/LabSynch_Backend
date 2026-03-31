from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChangePasswordView,
    MeView,
    MySchoolProfileView,
    SchoolProfileAdminViewSet,
    UserAdminViewSet,
)

router = DefaultRouter()
router.register(r"users", UserAdminViewSet, basename="user")
router.register(r"school-profiles", SchoolProfileAdminViewSet, basename="school-profile")

urlpatterns = [
    # Authenticated user's own endpoints — must be listed BEFORE the router
    # so that /users/me/ is matched before /users/<pk>/
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/me/school-profile/", MySchoolProfileView.as_view(), name="user-school-profile"),
    path("users/change-password/", ChangePasswordView.as_view(), name="user-change-password"),
    # Admin router endpoints
    path("", include(router.urls)),
]
