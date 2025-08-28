from django.contrib.auth.models import Permission
from django.conf import settings
from rest_framework import serializers
from .models import Team
from acct.serializers.fields import PrimaryKey_To_ObjectField
from apps.user.models import User


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "designation")


class TeamSerializer(serializers.ModelSerializer):
    heads = PrimaryKey_To_ObjectField(
        queryset=User.objects.all(),
        object_serializer=TeamMemberSerializer,
        many=True,
        required=False,
    )
    permissions = serializers.PrimaryKeyRelatedField(many=True, queryset=Permission.objects.all())
    # members is a list of user objects that belong to this team.
    members = TeamMemberSerializer(read_only=True, many=True)

    class Meta:
        model = Team
        fields = ("id", "name", "description", "members", "heads", "permissions")

    def to_representation(self, instance):
        """
        We override the default members repr. to use actual User objects
        instead of UserTenantPermissions
        """
        members = [user.profile for user in instance.user_set.all()]
        repr = super().to_representation(instance)
        repr["members"] = TeamMemberSerializer(members, many=True).data
        repr["permissions"] = self._get_perms_data(instance)
        return repr

    def validate_heads(self, value):
        if len(value) > Team.MAX_NUMBER_OF_HEADS:
            raise serializers.ValidationError(
                f"Max of {Team.MAX_NUMBER_OF_HEADS} users can head a team."
            )
        return value

    def create(self, validated_data):
        # heads should not be added on create
        validated_data.pop("heads", None)
        instance = super().create(validated_data)
        return instance

    def _get_perms_data(self, instance):
        """
        Return all team. permissions but, categorised by predefined
        categories in `settings.PERMISSION_CATEGORIES`.

        e.g:
        "sales": {
            "invoice": [
                {
                    "id": 1,
                    "name": "Can view invoice",
                    "codename": "view_invoice"
                }
            ]
        }
        """

        perms_categories = settings.PERMISSION_CATEGORIES
        perms_by_categories = {}
        for perm in instance.permissions.select_related("content_type"):
            perm_model = perm.content_type.name
            perm_dict = {"id": perm.id, "name": perm.name, "codename": perm.codename}
            for category, models in perms_categories.items():
                if perm_model not in models:
                    continue
                if category not in perms_by_categories:
                    perms_by_categories[category] = {}
                if perm_model in perms_by_categories[category]:
                    perms_by_categories[category][perm_model].append(perm_dict)
                else:
                    perms_by_categories[category][perm_model] = [perm_dict]
        return perms_by_categories


class UpdateTeamMembersSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    def update_members(self, instance, validated_data):
        action = self.context["action"]
        user_ids = validated_data["users"]
        users = User.objects.filter(id__in=user_ids)
        if users:
            if action == "add":
                response = instance.add_members(users)
            elif action == "remove":
                response = instance.remove_members(users)
            else:
                raise ValueError(f"Invalid action type'{action}'")
            return response
        else:
            raise serializers.ValidationError("No valid user sent.")


class TeamPermissionSerializer(serializers.ModelSerializer):
    module = serializers.CharField(source="content_type.app_label")
    model = serializers.CharField(source="content_type.model")

    class Meta:
        model = Permission
        fields = ("id", "name", "codename", "module", "model")


class TeamAsRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("id", "name")
