from rest_framework.viewsets import ModelViewSet
from apps.purchase.expense.models import Expense
from apps.purchase.expense.serializers import ExpenseSerializer
from apps.accounting.models import Transaction


class ExpenseViewSet(ModelViewSet):
    queryset = Expense.objects
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        Transaction.objects.record_expense(serializer.save())

    def perform_update(self, serializer):
        Transaction.objects.record_expense(serializer.save())

    def perform_destroy(self, instance):
        Transaction.objects.delete_resource(instance)
        super().perform_destroy(instance)
