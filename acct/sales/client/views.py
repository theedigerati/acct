from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from apps.sales.client.models import Client
from apps.sales.client.serializers import ClientSerializer


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filter_backends = [SearchFilter]
    search_fields = ["display_name", "business_name", "full_name"]
