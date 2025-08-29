from rest_framework import serializers
from apps.purchase.expense.models import Expense
from apps.tax.models import Tax
from apps.accounting.models import Account
from apps.accounting.serializers import AccountShallowSerializer
from apps.tax.serializers import TaxSerializer
from apps.purchase.vendor.models import Vendor
from apps.purchase.vendor.serializers import VendorShallowSerializer
from acct.serializers.fields import PrimaryKey_To_ObjectField


class ExpenseSerializer(serializers.ModelSerializer):
    amount_incl_tax = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    vendor = PrimaryKey_To_ObjectField(
        queryset=Vendor.objects,
        object_serializer=VendorShallowSerializer,
        allow_null=True,
        required=False,
    )
    account = PrimaryKey_To_ObjectField(
        queryset=Account.actives, object_serializer=AccountShallowSerializer
    )
    paid_through = PrimaryKey_To_ObjectField(
        queryset=Account.actives, object_serializer=AccountShallowSerializer
    )
    taxes = PrimaryKey_To_ObjectField(
        queryset=Tax.objects,
        object_serializer=TaxSerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = Expense
        exclude = ("created_at",)
