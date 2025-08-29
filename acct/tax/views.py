from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from .models import Tax
from .serializers import TaxSerializer


class TaxViewSet(ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer

    @action(["post"], detail=False)
    def bulk_create_or_update(self, request):
        data = request.data
        self.saved_taxes = []
        for tax_data in data:
            tax_id = tax_data.get("id")
            if tax_id is not None:
                try:
                    tax = Tax.objects.get(id=tax_id)
                    serializer = self.serializer_class(tax, data=tax_data)
                except Tax.DoesNotExist:
                    serializer = self.serializer_class(data=tax_data)

                self._save_taxes(serializer)
            else:
                serializer = self.serializer_class(data=tax_data)
                self._save_taxes(serializer)

        return Response(self.saved_taxes, status=status.HTTP_201_CREATED)

    def _save_taxes(self, serializer):
        if serializer.is_valid():
            serializer.save()
            self.saved_taxes.append(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
