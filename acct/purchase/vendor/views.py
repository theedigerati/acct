from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from apps.purchase.vendor.models import Vendor
from apps.purchase.vendor.serializers import VendorSerializer


class VendorViewSet(ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [SearchFilter]
    search_fields = ["display_name", "business_name", "full_name"]
