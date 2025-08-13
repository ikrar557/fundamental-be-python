from rest_framework.permissions import BasePermission

from core.models import User
from events.models import Event


class IsSuperUser(BasePermission):
    """
    Allows access to superusers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

class IsAdmin(BasePermission):
    """
    Allows access to admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='admin').exists()

class IsOrganizer(BasePermission):
    """
    Allows access to organizer.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='organizer').exists()

class IsAdminOrSuperUser(BasePermission):
    """
    Allows access to admin and superusers.
    """
    def has_permission(self, request, view):
      return (
          request.user and request.user.is_authenticated and (
              request.user.is_superuser or
              request.user.groups.filter(name='admin').exists()
          )
      )

class IsAdminOrOrganizerOrSuperUser(BasePermission):
    """
    Allows access to admin, organizer, and superusers.
    """
    def has_permission(self, request, view):
      return (
          request.user and request.user.is_authenticated and (
              request.user.is_superuser or
              request.user.groups.filter(name='admin').exists() or
              request.user.groups.filter(name='organizer').exists()
          )
      )

class IsOwnerOrAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.groups.filter(name='admin').exists():
            return True

        if isinstance(obj, Event):
            try:
                return obj.organizer_id.id == request.user.id
            except AttributeError:
                return False

        elif isinstance(obj, User):
            return obj == request.user

        return False


