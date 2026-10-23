from rest_framework.permissions import BasePermission

from accounts.models import Role


class IsAdminRole(BasePermission):
    message = "Admin role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == Role.ADMIN)
