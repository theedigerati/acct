from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.exceptions import PermissionDenied


def belongs_to_organisation(request):
    if request.user and request.user.is_authenticated:
        try:
            return bool(request.user.tenant_perms)
        except ObjectDoesNotExist:
            raise PermissionDenied("You do not have permission to access this organisation.")
    else:
        return False


class BelongsToOrganisation(BasePermission):
    """
    Allow access to only authenticated users that
    belong to the organisation tenant from the request.
    """

    def has_permission(self, request, view):
        return belongs_to_organisation(request)


class IsManagerOrMore(BasePermission):
    """
    Allow access to users with access role of MANAGER, ADMIN or OWNER
    that satisty BelongsToOrganisation.
    """

    def has_permission(self, request, view):
        if belongs_to_organisation(request):
            return bool(request.user.is_manager_or_more)
        else:
            return False


class IsAdmin(BasePermission):
    """
    Allow access to users with access role ADMIN or OWNER
    that satisty BelongsToOrganisation.
    """

    def has_permission(self, request, view):
        if belongs_to_organisation(request):
            return bool(request.user.is_admin_or_more)
        else:
            return False


class IsOwner(BasePermission):
    """
    Allow access to users with access role OWNER
    that satisty BelongsToOrganisation.
    """

    def has_permission(self, request, view):
        if belongs_to_organisation(request):
            return bool(request.user.is_owner)
        else:
            return False


class BaseModelPermissions(DjangoModelPermissions):
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }
