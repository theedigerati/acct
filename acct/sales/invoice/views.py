from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.accounting.models import Transaction
from apps.sales.invoice.models import Invoice, InvoiceStatus, PaymentReceived
from apps.sales.invoice.serializers import InvoiceSerializer, PaymentReceivedSerializer


class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

    def get_serializer_class(self):
        if self.action in ["move_to_draft", "mark_as_sent", "outstanding"]:
            return None
        return self.serializer_class

    def perform_create(self, serializer):
        self.record_transaction(serializer.save())

    def perform_update(self, serializer):
        self.record_transaction(serializer.save())

    def perform_destroy(self, instance):
        if instance.status is not InvoiceStatus.DRAFT:
            return Response(
                "Sent Invoice cannot be deleted", status=status.HTTP_400_BAD_REQUEST
            )
        super().perform_destroy(instance)

    @action(["post"], detail=True)
    def move_to_draft(self, request, pk=None):
        self.get_object().move_to_draft()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=True)
    def mark_as_sent(self, request, pk=None):
        self.get_object().mark_as_sent()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False)
    def outstanding(self, request):
        return Response(Invoice.objects.get_outstanding())

    def record_transaction(self, instance):
        if instance.status is not InvoiceStatus.DRAFT:
            Transaction.objects.record_invoice(instance)


class PaymentReceivedViewSet(ModelViewSet):
    queryset = PaymentReceived.objects.all()
    serializer_class = PaymentReceivedSerializer

    def get_queryset(self):
        queryset = self.queryset
        invoice_id = self.request.query_params.get("invoice")
        if invoice_id is not None:
            queryset = (
                queryset.filter(invoice__id=int(invoice_id)) if invoice_id else queryset
            )
        return queryset

    def perform_create(self, serializer):
        Transaction.objects.record_payment_received(serializer.save())

    def perform_update(self, serializer):
        Transaction.objects.record_payment_received(serializer.save())

    def perform_destroy(self, instance):
        Transaction.objects.delete_resource(instance)
        super().perform_destroy(instance)
