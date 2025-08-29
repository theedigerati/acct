from rest_framework import serializers
from apps.inventory.item.models import Item
from apps.user.models import User


class SaleItemSerializer(serializers.ModelSerializer):
    rate = serializers.DecimalField(
        source="selling_price", decimal_places=2, max_digits=16
    )

    class Meta:
        model = Item
        fields = ("id", "type", "name", "description", "rate")


class SalesPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name")


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"
