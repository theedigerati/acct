from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.purchase.bill.models import Bill, BillStatus, PaymentMade
from apps.purchase.bill.serializers import BillSerializer, PaymentMadeSerializer
from apps.accounting.models import Transaction


class BillViewSet(ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    def get_serializer_class(self):
        if self.action in ["move_to_draft", "mark_as_open"]:
            return None
        return self.serializer_class

    def perform_create(self, serializer):
        self.record_transaction(serializer.save())

    def perform_update(self, serializer):
        self.record_transaction(serializer.save())

    @action(["post"], detail=True)
    def move_to_draft(self, request, pk=None):
        self.get_object().move_to_draft()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["post"], detail=True)
    def mark_as_open(self, request, pk=None):
        self.get_object().mark_as_open()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=False)
    def outstanding(self, request):
        return Response(Bill.objects.get_outstanding())

    def record_transaction(self, instance):
        if instance.status is not BillStatus.DRAFT:
            Transaction.objects.record_bill(instance)


class PaymentMadeViewSet(ModelViewSet):
    queryset = PaymentMade.objects.all()
    serializer_class = PaymentMadeSerializer

    def get_queryset(self):
        queryset = self.queryset
        bill_id = self.request.query_params.get("bill")
        if bill_id is not None:
            queryset = queryset.filter(bill__id=int(bill_id)) if bill_id else queryset
        return queryset

    def perform_create(self, serializer):
        Transaction.objects.record_payment_made(serializer.save())

    def perform_update(self, serializer):
        Transaction.objects.record_payment_made(serializer.save())

    def perform_destroy(self, instance):
        Transaction.objects.delete_resource(instance)
        super().perform_destroy(instance)
