from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from apps.accounting.models import (
    Account,
    AccountSubType,
    JournalEntry,
    Transaction,
)
from apps.accounting.serializers import (
    AccountSerializer,
    AccountSiblingsSerializer,
    AccountSubTypeSerializer,
    JournalEntrySerializer,
    TransactionSerializer,
)


class AccountViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get_serializer_class(self):
        if self.action == "siblings":
            return AccountSiblingsSerializer
        if self.action == "transactions":
            return TransactionSerializer
        return self.serializer_class

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.editable:
            return Response(
                "This account cannot be deleted because it is used for automated transactions.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get"], detail=True)
    def siblings(self, request, *args, **kwargs):
        # siblings data is generated in the serializer
        return self.retrieve(request, *args, **kwargs)

    @action(["get"], detail=True)
    def transactions(self, request, *args, **kwargs):
        insance = self.get_object()
        serializer = self.get_serializer(insance.transactions.all(), many=True)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def subtypes(self, request, *args, **kwargs):
        serializer = AccountSubTypeSerializer(AccountSubType.objects.all(), many=True)
        return Response(serializer.data)

    @action(["get"], detail=False)
    def balance(self, request, *args, **kwargs):
        accounts = Account.actives.values(
            "id", bal=Sum("transactions__amount", default=0)
        )
        return Response(
            {
                account["id"]: account["bal"] if account["bal"] else 0
                for account in accounts
            }
        )


class JournalEntryViewSet(ModelViewSet):
    queryset = JournalEntry.objects
    serializer_class = JournalEntrySerializer

    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        request.data["created_by"] = request.user.id
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        self.record_transaction(serializer.save())

    @action(["post"], detail=True)
    def mark_as_published(self, request, *args, **kwargs):
        self.get_object().mark_as_published()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def record_transaction(self, instance):
        if not instance.is_draft:
            Transaction.objects.record_journal_entry(instance)
