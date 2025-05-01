from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions

from apps.user.serializers import PermissionSerializer
from .models import Team
from .serializers import (
    TeamMemberSerializer,
    TeamSerializer,
    UpdateTeamMembersSerializer,
)
from core.permissions import BelongsToOrganisation, BaseModelPermissions


class UpdateTeamAsHead(DjangoModelPermissions):
    """
    Ensures that rquest user has the permission of a team head,
    belongs to the team and is one the heads.
    """

    perms_map = {
        "GET": ["%(app_label)s.custom_change_team_as_head"],
        "OPTIONS": ["%(app_label)s.custom_change_team_as_head"],
        "HEAD": ["%(app_label)s.custom_change_team_as_head"],
        "POST": ["%(app_label)s.custom_change_team_as_head"],
        "PUT": ["%(app_label)s.custom_change_team_as_head"],
        "PATCH": ["%(app_label)s.custom_change_team_as_head"],
    }

    def has_object_permission(self, request, view, obj):
        request_user_is_member = obj.user_set.filter(profile__id=request.user.id).exists()
        request_user_is_head = obj.heads.filter(id=request.user.id).exists()
        return request_user_is_member and request_user_is_head


class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_permissions(self):
        if self.action in [
            "update",
            "partial_update",
            "add_members",
            "remove_members",
            "all_permissions",
            "non_members",
        ]:
            self.permission_classes = [
                BelongsToOrganisation,
                UpdateTeamAsHead | BaseModelPermissions,
            ]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [BelongsToOrganisation, DjangoModelPermissions]
        return super().get_permissions()

    def check_object_permissions(self, request, obj):
        """
        Only mgt. users can update team. permissions.
        i.e only users with the 'change_team' permission.
        """
        is_update_request = self.action == "update" or self.action == "partial_update"
        if is_update_request and "permissions" in request.data:
            # check that it is an update
            team_permissions_data = request.data.get("permissions", [])
            current_team_permissions = obj.permissions.values_list("id", flat=True)
            is_updating_permissions = set(team_permissions_data) != set(current_team_permissions)

            if is_updating_permissions and request.user.has_perm("team.change_team") is False:
                raise PermissionDenied("You're not permitted to update this team's permissions.")

        return super().check_object_permissions(request, obj)

    @action(methods=["get"], detail=True)
    def all_permissions(self, request, pk=None):
        instance = self.get_object()
        permissions = instance.permissions.all()
        ser = PermissionSerializer(permissions, many=True)
        return Response(ser.data)

    @action(methods=["post"], detail=True)
    def add_members(self, request, pk=None):
        response = self._update_members(request, "add")
        return Response(response)

    @action(methods=["post"], detail=True)
    def remove_members(self, request, pk=None):
        response = self._update_members(request, "remove")
        return Response(response)

    @action(methods=["get"], detail=True)
    def non_members(self, request, pk=None):
        instance = self.get_object()
        members = instance.user_set.values_list("profile__id", flat=True)
        non_members = request.tenant.user_set.exclude(id__in=members)
        serializer = TeamMemberSerializer(non_members, many=True)
        return Response(serializer.data)

    def _update_members(self, request, action_type):
        instance = self.get_object()
        ser = UpdateTeamMembersSerializer(
            instance, data=request.data, context={"action": action_type}
        )
        if ser.is_valid(raise_exception=True):
            response = ser.update_members(instance, ser.validated_data)
            return response


# TODO: add view action to deactivate team.
