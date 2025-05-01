import contextlib
from django.conf import settings
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from django_tenants.utils import schema_context
from apps.team.models import Team
from core.permissions import BelongsToOrganisation
from .models import User
from .serializers import (
    UserSerializer,
    UserCreateUnsafeSerializer,
    UserLazyUpdateSerializer,
    Permission,
    PermissionSerializer,
)


class CustomModelPermissions(DjangoModelPermissions):
    """
    Enforce role hierarchy access.
    """

    def has_permission(self, request, view):
        has_perms = super().has_permission(request, view)
        if view.action == "create":
            return has_perms and view.can_assign_role(request, request.data.get("role"))
        return has_perms

    def has_object_permission(self, request, view, obj):
        if view.action == "permissions" and obj == request.user:
            return True

        can_retrieve_user = view.can_retrieve_user(request, obj)
        if view.action == "retrieve":
            return can_retrieve_user

        can_assign_role = view.can_assign_role(request, request.data.get("role"))
        can_update_user = view.can_update_user(request, obj)
        can_update = can_retrieve_user and can_update_user and can_assign_role

        if view.action == "permissions":
            return request.user.has_perm("user.change_user") and can_update

        if view.action in ["update", "partial_update", "permissions"]:
            return can_update

        return True


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [BelongsToOrganisation, CustomModelPermissions]

    def get_queryset(self):
        """
        Return users in the request tenant.
        """
        queryset = self.queryset
        tenant = self.request.tenant
        user_ids = tenant.user_set.values_list("id", flat=True)
        return queryset.filter(id__in=user_ids)

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = [IsAuthenticated]
        if self.action == "my_permissions":
            self.permission_classes = [BelongsToOrganisation]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "me" and (
            self.request.method == "PUT" or self.request.method == "PATCH"
        ):
            return UserLazyUpdateSerializer
        return self.serializer_class

    @schema_context("public")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.delete(force_drop=True)

    @action(["get", "put", "patch"], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        if request.method == "GET":
            return self.retrieve(request, *args, **kwargs)
        elif request.method == "PUT":
            return self.update(request, *args, **kwargs)
        elif request.method == "PATCH":
            return self.partial_update(request, *args, **kwargs)

    @action(["get"], detail=False)
    def my_permissions(self, request, *args, **kwargs):
        perms = request.user.get_all_permissions()
        return Response([perm.split(".")[1] for perm in perms])

    @action(["get"], detail=True)
    def permissions(self, request, *args, **kwargs):
        instance = self.get_object()
        serialized_perms = self.get_serialized_permissions(instance)
        return Response(serialized_perms)

    @action(methods=["post"], detail=False)
    def unsafe_create(self, request, *args, **kwargs):
        ser = UserCreateUnsafeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        with schema_context("public"):
            user = ser.save()
        # add user to the request tenant and asssign permissions
        request.tenant.add_user(user)
        user.assign_default_permissions()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def get_instance(self):
        return self.request.user

    def get_serialized_permissions(self, user):
        perms = user.get_all_permissions()
        permissions = Permission.objects.filter(
            codename__in=[perm.split(".")[1] for perm in perms]
        )
        ser = PermissionSerializer(permissions, many=True)
        return ser.data

    def can_retrieve_user(self, request, user):
        """
        Check if request user and `user` both belong
        to the request tenant.
        """
        tenants_for_user = user.tenants.exclude(schema_name="public")
        tenants_for_request_user = request.user.tenants.exclude(schema_name="public")
        return bool(tenants_for_user.intersection(tenants_for_request_user))

    def can_assign_role(self, request, role):
        """
        Check if request user has hierarchy access to assign `role` to a user.
        """
        if role is None:
            return True

        if (
            (request.user.is_employee and role != User.EMPLOYEE)
            or (request.user.is_admin and role == User.OWNER)
            or (request.user.is_manager and role in [User.ADMIN, User.OWNER])
        ):
            return False

        return True

    def can_update_user(self, request, user):
        """
        Check if request user has hierarchy access to update `user`.
        """
        if (
            (request.user.is_employee and user.is_manager_or_more)
            or (request.user.is_admin and user.is_owner)
            or (request.user.is_manager and user.is_admin_or_more)
        ):
            return False

        return True

    # TODO: 6 Tasks
    #
    # 1. Implement user activation.
    # 2. Implement user resend activation.
    # 3. Implement user reset password.
    # 4. Implemrnt user reset password confirm.
    # 5. Implement admin reset password.
    # 6. Implement deactivate user.


class PermissionSourceOfTruthPermissions(DjangoModelPermissions):
    perms_map = {"GET": ["user.change_user", "team.change_team"]}


class PermissionViewSet(ModelViewSet):
    queryset = Permission.objects.exclude(
        content_type__app_label__in=["admin", "auth", "contenttypes"]
    ).select_related("content_type")
    serializer_class = PermissionSerializer

    def get_permissions(self):
        if self.action == "source_of_truth":
            self.permission_classes = [
                BelongsToOrganisation,
                PermissionSourceOfTruthPermissions,
            ]
        return super().get_permissions()

    @action(["get"], detail=False)
    def source_of_truth(self, request, *args, **kwargs):
        """
        Return all available permissions but, categorised by predefined
        categories in `settings.PERMISSION_CATEGORIES`.

        Add an `active` bool flag on each permissions indicating that a
        user or team has been assigned the permission.

        Add an `inherited` bool flag on each permissions indicating that
        a user has inherited the permission from a team. Default will
        be false for all teams.

        If user or team id value is not provided in request query params,
        `active` & `inherited` flags will be false.

        e.g:
        "sales": {
            "invoice": [
                {
                    "perm": {
                        "id": 1,
                        "name": "Can view invoice",
                        "codename": "view_invoice"
                    }
                    "active": True,
                    "inherited": True,
                }
            ]
        }
        """
        perms_categories = settings.PERMISSION_CATEGORIES
        perms_by_categories = {}
        for perm in self.queryset:
            perm_model = perm.content_type.name
            for category, models in perms_categories.items():
                if perm_model not in models:
                    continue
                if category not in perms_by_categories:
                    perms_by_categories[category] = {}
                perm_data = self._get_perm_data(request, perm)
                if perm_model in perms_by_categories[category]:
                    perms_by_categories[category][perm_model].append(perm_data)
                else:
                    perms_by_categories[category][perm_model] = [perm_data]
        return Response(perms_by_categories)

    def _get_perm_data(self, request, perm):
        user_id = request.query_params.get("user", 0)
        team_id = request.query_params.get("team", 0)
        user_object = None
        team_object = None

        with contextlib.suppress(User.DoesNotExist):
            user_object = User.objects.get(id=int(user_id))
        with contextlib.suppress(Team.DoesNotExist):
            team_object = Team.objects.get(id=int(team_id))

        perm_dict = {"id": perm.id, "name": perm.name, "codename": perm.codename}

        if user_object:
            perm_string = f"{perm.content_type.app_label}.{perm.codename}"
            return {
                "perm": perm_dict,
                "active": user_object.has_perm(perm_string),
                "inherited": perm_string in user_object.get_group_permissions(),
            }

        if team_object:
            return {
                "perm": perm_dict,
                "active": team_object.permissions.filter(id=perm.id).exists(),
                "inherited": False,
            }

        return {"perm": perm_dict, "active": False, "inherited": False}
