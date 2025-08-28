from django.db import transaction
from rest_framework import serializers
from apps.tax.models import Tax
from apps.tax.serializers import TaxSerializer
from apps.inventory.item.models import Item
from apps.inventory.item.serializers import SaleItemSerializer
from apps.purchase.vendor.models import Vendor
from apps.purchase.vendor.serializers import VendorSerializer
from apps.purchase.bill.models import Bill, BillLine, BillStatus, PaymentMade
from acct.serializers.fields import PrimaryKey_To_ObjectField
from acct.serializers.utils import CreateUpdateRelationMixin


class BillLineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    item = PrimaryKey_To_ObjectField(
        queryset=Item.objects,
        object_serializer=SaleItemSerializer,
        allow_null=True,
        required=False,
    )
    taxes = PrimaryKey_To_ObjectField(
        queryset=Tax.objects,
        object_serializer=TaxSerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = BillLine
        exclude = ("bill",)


class BaseBillSerializer(CreateUpdateRelationMixin, serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=BillStatus.choices, read_only=True)
    vendor = PrimaryKey_To_ObjectField(queryset=Vendor.objects, object_serializer=VendorSerializer)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(
        source="total_incl_tax", max_digits=12, decimal_places=2, read_only=True
    )
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"


class BillSerializer(BaseBillSerializer):
    lines = BillLineSerializer(many=True, required=False)

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


class PaymentBillSerializer(serializers.ModelSerializer):
    vendor = serializers.CharField(source="vendor.display_name")

    class Meta:
        model = Bill
        fields = ("id", "number", "vendor")


class PaymentMadeSerializer(serializers.ModelSerializer):
    bill = PrimaryKey_To_ObjectField(
        queryset=Bill.objects,
        allow_null=True,
        required=False,
        object_serializer=PaymentBillSerializer,
    )

    class Meta:
        model = PaymentMade
        fields = "__all__"
