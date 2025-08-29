from celery.result import AsyncResult
from rest_framework.views import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions
from acct.permissions import BelongsToOrganisation
from .models import Organisation
from .serializers import (
    OrganisationSerializer,
    OrganisationUsersUpdateSerializer,
)
from .tasks import setup_org_tenancy


class AddRemoveUsers(DjangoModelPermissions):
    perms_map = {"POST": ["%(app_label)s.custom_update_users"]}


class ViewAllOrganisations(DjangoModelPermissions):
    perms_map = {"GET": ["%(app_label)s.custom_view_all_organisations"]}


class OrganisationViewSet(ModelViewSet):
    queryset = Organisation.objects.all()
    serializer_class = OrganisationSerializer

    def get_permissions(self):
        if self.action == "add_users" or self.action == "remove_users":
            self.permission_classes = [BelongsToOrganisation, AddRemoveUsers]
        if self.action == "list":
            self.permission_classes = [BelongsToOrganisation, ViewAllOrganisations]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task_id = self.perform_create(request, serializer)
        serializer_data = serializer.data
        serializer_data.update({"task_id": str(task_id)})
        headers = self.get_success_headers(serializer_data)
        return Response(serializer_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, request, serializer):
        instance = serializer.save()
        task_id = setup_org_tenancy.delay(instance.id, request.user.id)
        Organisation.objects.filter(id=instance.id).update(task_id=str(task_id))
        return task_id

    @action(methods=["post"], detail=False)
    def add_users(self, request):
        response = self._update_users(request, "add")
        return Response(response)

    @action(methods=["post"], detail=False)
    def remove_users(self, request):
        response = self._update_users(request, "remove")
        return Response(response)

    @action(["get"], detail=True)
    def task_status(self, request, pk=None):
        """Get tenancy setup celery task status"""

        instance = self.get_object()
        if instance.task_id is None:
            return Response("No tenancy task available", status=status.HTTP_400_BAD_REQUEST)
        task_result = AsyncResult(instance.task_id)
        result = {
            "id": instance.task_id,
            "status": task_result.status,
        }
        return Response(result)

    def _update_users(self, request, action_type):
        instance = request.tenant.organisation
        ser = OrganisationUsersUpdateSerializer(
            instance, data=request.data, context={"action": action_type}
        )
        if ser.is_valid(raise_exception=True):
            response = ser.update_users(instance, ser.validated_data)
            return response

    # TODO: implement disable Org.
