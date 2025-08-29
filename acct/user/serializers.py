from django.db import IntegrityError, transaction
from django.contrib.auth.models import Permission
from rest_framework import serializers
from .models import User
from apps.organisation.models import Organisation
from apps.organisation.serializers import OrganisationSerializer


class UserSerializer(serializers.ModelSerializer):
    organisations = OrganisationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "full_name",
            "designation",
            "email",
            "role",
            "is_verified",
            "is_active",
            "organisations",
        )
        read_only_fields = ["full_name", "is_verified", "is_active", "organisations"]

    # user model has no direct relation to org, only reverse relation to renants
    def to_representation(self, instance):
        tenant_ids = instance.tenants.values_list("id", flat=True)
        organisations = Organisation.objects.filter(tenant__id__in=tenant_ids)
        repr = super().to_representation(instance)
        repr["organisations"] = OrganisationSerializer(organisations, many=True).data
        return repr

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)

                # TODO: Send user activation email.
        except IntegrityError:
            self.fail("cannot_create_user")
        return user


class UserLazyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )


class UserCreateUnsafeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, allow_blank=True, default="password"
    )

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "password",
            "full_name",
            "designation",
            "email",
            "role",
        )
        read_only_fields = ["id", "full_name"]

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(**validated_data)
                user.is_verified = True
                user.save(update_fields=["is_verified"])
        except IntegrityError:
            self.fail("cannot_create_user")
        return user


class PermissionSerializer(serializers.ModelSerializer):
    model = serializers.CharField(source="content_type.name")
    module = serializers.CharField(source="content_type.app_label")

    class Meta:
        model = Permission
        fields = ("id", "name", "codename", "model", "module")


class UserAsRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name")
