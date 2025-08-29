from django.db import models


class InvoiceManager(models.Manager):
    def get_outstanding(self):
        """
        Calculate amount due for all unarchived invoices.
        """
        draft, overdue, total = 0, 0, 0
        for invoice in (
            self.get_queryset()
            .filter(archived=False)
            .prefetch_related("lines", "payments")
        ):
            if invoice.is_draft:
                draft += invoice.amount_due
                continue
            if invoice.is_overdue:
                overdue += invoice.amount_due
            total += invoice.amount_due
        return {"draft": draft, "overdue": overdue, "total": total}


class PaymentReceivedManager(models.Manager):
    def create(self, **kwargs):
        instance = super().create(**kwargs)
        if instance.invoice.is_draft:
            instance.invoice.is_draft = False
            instance.invoice.save()
        return instance
