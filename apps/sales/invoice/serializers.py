from django.db import transaction
from rest_framework import serializers
from apps.tax.models import Tax
from apps.tax.serializers import TaxSerializer
from apps.inventory.item.models import Item
from apps.inventory.item.serializers import SaleItemSerializer, SalesPersonSerializer
from apps.sales.client.models import Client
from apps.sales.client.serializers import ClientSerializer
from apps.sales.invoice.models import (
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    PaymentReceived,
)
from apps.user.models import User
from acct.serializers.fields import PrimaryKey_To_ObjectField
from acct.serializers.utils import CreateUpdateRelationMixin


class InvoiceLineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    item = PrimaryKey_To_ObjectField(queryset=Item.objects, object_serializer=SaleItemSerializer)
    taxes = PrimaryKey_To_ObjectField(
        queryset=Tax.objects,
        object_serializer=TaxSerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = InvoiceLine
        exclude = ("invoice",)


class BaseInvoiceSerializer(CreateUpdateRelationMixin, serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=InvoiceStatus.choices, read_only=True)
    client = PrimaryKey_To_ObjectField(queryset=Client.objects, object_serializer=ClientSerializer)
    salesperson = PrimaryKey_To_ObjectField(
        allow_null=True,
        required=False,
        queryset=User.objects.all(),
        object_serializer=SalesPersonSerializer,
    )
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(
        source="total_incl_tax", max_digits=12, decimal_places=2, read_only=True
    )
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"


class InvoiceSerializer(BaseInvoiceSerializer):
    lines = InvoiceLineSerializer(many=True, required=False)

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


class PaymentInvoiceSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="client.display_name")

    class Meta:
        model = Invoice
        fields = ("id", "number", "client")


class PaymentReceivedSerializer(serializers.ModelSerializer):
    invoice = PrimaryKey_To_ObjectField(
        queryset=Invoice.objects,
        allow_null=True,
        required=False,
        object_serializer=PaymentInvoiceSerializer,
    )

    class Meta:
        model = PaymentReceived
        fields = "__all__"
