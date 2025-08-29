from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework import filters
from apps.inventory.item.models import Item
from apps.inventory.item.serializers import ItemSerializer
from django_filters.rest_framework import DjangoFilterBackend


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.filter(type="goods")
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    filter_fields = ["is_active"]


class ServiceViewSet(ModelViewSet):
    queryset = Item.objects.filter(type="service")
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    filter_fields = ["is_active"]


class ItemsAndServicesList(ListAPIView):
    queryset = Item.objects.filter(is_active=True)
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
