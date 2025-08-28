from django.db import transaction
from rest_framework import serializers
from apps.accounting.models import (
    Account,
    AccountSubType,
    JournalEntry,
    JournalEntryLine,
    Transaction,
    TransactionType,
)
from apps.user.models import User
from apps.user.serializers import UserAsRelationSerializer
from acct.serializers.fields import PrimaryKey_To_ObjectField
from acct.serializers.utils import CreateUpdateRelationMixin


class AccountSubTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountSubType
        exclude = ("created_at",)


class AccountShallowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("id", "name")


class AccountSerializer(serializers.ModelSerializer):
    sub_type = PrimaryKey_To_ObjectField(
        queryset=AccountSubType.objects.all(),
        object_serializer=AccountSubTypeSerializer,
    )

    class Meta:
        model = Account
        fields = (
            "id",
            "name",
            "code",
            "description",
            "sub_type",
            "parent",
            "is_archived",
            "editable",
        )

    def update(self, instance, validated_data):
        if not instance.editable:
            raise serializers.ValidationError(
                "This account cannot be edited because it is used for automated transactions"
            )
        return super().update(instance, validated_data)


class AccountSiblingsSerializer(serializers.ModelSerializer):
    sub_types = AccountSubTypeSerializer(many=True, read_only=True)
    accounts = AccountSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = ("sub_types", "accounts")

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        repr["sub_types"] = AccountSubTypeSerializer(instance.sibling_sub_types, many=True).data
        repr["accounts"] = AccountSerializer(instance.sibling_accounts, many=True).data
        return repr


class TransactionSerializer(serializers.ModelSerializer):
    account = serializers.SlugRelatedField(slug_field="name", read_only=True)
    ref_type = serializers.SlugRelatedField(slug_field="model", read_only=True)

    class Meta:
        model = Transaction
        fields = "__all__"


class JournalEntryLineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    account = PrimaryKey_To_ObjectField(
        queryset=Account.actives, object_serializer=AccountShallowSerializer
    )

    class Meta:
        model = JournalEntryLine
        exclude = ("journal",)


class JournalEntrySerializer(CreateUpdateRelationMixin, serializers.ModelSerializer):
    created_by = PrimaryKey_To_ObjectField(
        queryset=User.objects, object_serializer=UserAsRelationSerializer
    )
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    lines = JournalEntryLineSerializer(many=True, required=False)

    class Meta:
        model = JournalEntry
        fields = "__all__"

    def validate_lines(self, value):
        """
        Check that journal entry is valid & balanced.
        """

        if len(value) < 2:
            raise serializers.ValidationError(
                "At least a debit and credit entry should be provided!"
            )

        total_debit = 0
        total_credit = 0

        for line in value:
            if line["type"] == TransactionType.DEBIT:
                total_debit += line["amount"]
            if line["type"] == TransactionType.CREDIT:
                total_credit += line["amount"]
        if total_debit != total_credit:
            raise serializers.ValidationError("Journal Entry not balanced!")
        return value

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", None)
        with transaction.atomic():
            self.instance = instance = super().create(validated_data)
            return self.update(instance, dict(validated_data, lines=lines_data))

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            self.update_relation("lines", instance.lines, lines_data)
            return instance
