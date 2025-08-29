from django.db import models


class BillManager(models.Manager):
    def get_outstanding(self):
        """
        Calculate amount due for all unarchived bills.
        """
        draft, overdue, total = 0, 0, 0
        for bill in (
            self.get_queryset()
            .filter(archived=False)
            .prefetch_related("lines", "payments")
        ):
            if bill.is_draft:
                draft += bill.amount_due
                continue
            if bill.is_overdue:
                overdue += bill.amount_due
            total += bill.amount_due
        return {"draft": draft, "overdue": overdue, "total": total}


class PaymentMadeManager(models.Manager):
    def create(self, **kwargs):
        instance = super().create(**kwargs)
        if instance.bill.is_draft:
            instance.bill.is_draft = False
            instance.bill.save()
        return instance
