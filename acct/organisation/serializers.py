from rest_framework import serializers
from .models import OrgAddress, Organisation
from apps.user.models import User


class OrgAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgAddress
        fields = "__all__"


class OrganisationSerializer(serializers.ModelSerializer):
    address = OrgAddressSerializer()
    domain_slug = serializers.CharField(read_only=True)
    users = serializers.IntegerField(read_only=True)

    class Meta:
        model = Organisation
        exclude = ("tenant",)
        read_only_fields = ("task_id",)

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        instance = super().create(validated_data)
        # create address
        address_serializer = self.fields["address"]
        instance.address = address_serializer.create(address_data)
        instance.save()
        # add request user to org members
        request_user = self.context.get("view").request.user
        instance.add_users([request_user])
        return instance

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        instance = super().update(instance, validated_data)
        # adrress_data may be None due to partial update
        if address_data:
            address_serializer = self.fields["address"]
            instance.address = address_serializer.update(instance.address, address_data)
            instance.save()
        return instance


class OrganisationUsersUpdateSerializer(serializers.Serializer):
    users = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    def update_users(self, instance, validated_data):
        action = self.context["action"]
        user_ids = validated_data["users"]
        users = User.objects.filter(id__in=user_ids)
        if users:
            if action == "add":
                response = instance.add_users(users)
            elif action == "remove":
                response = instance.remove_users(users)
            else:
                raise ValueError(f"Invalid action type'{action}'")
            return response
        else:
            raise serializers.ValidationError("No valid user sent.")
