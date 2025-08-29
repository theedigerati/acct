from rest_framework.serializers import ModelSerializer
from apps.address.serializers import AddressSerializer
from apps.sales.client.models import Client


class ClientShallowSerializer(ModelSerializer):
    class Meta:
        model = Client
        fields = ("id", "display_name")


class ClientSerializer(ModelSerializer):
    shipping_address = AddressSerializer(required=False)

    class Meta:
        model = Client
        fields = "__all__"

    def create(self, validated_data):
        shipping_address_data = validated_data.pop("shipping_address", None)
        instance = super().create(validated_data)
        if shipping_address_data:
            address_serializer = self.fields["shipping_address"]
            instance.shipping_address = address_serializer.create(shipping_address_data)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        shipping_address_data = validated_data.pop("shipping_address", None)
        instance = super().update(instance, validated_data)
        if shipping_address_data:
            address_serializer = self.fields["shipping_address"]
            if instance.shipping_address:
                instance.shipping_address = address_serializer.update(
                    instance.shipping_address, shipping_address_data
                )
            else:
                instance.shipping_address = address_serializer.create(
                    shipping_address_data
                )
            instance.save()
        return instance
