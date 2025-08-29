from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from django.apps import apps
from .managers import InvoiceManager, PaymentReceivedManager
from acct.utils import get_next_number


def get_invoice_next_number():
    return get_next_number(Invoice, Invoice.NUMBER_PREFIX)


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft - Generated but not sent to the client."
    SENT = "sent", "Sent"
    PARTLY_PAID = "partly paid", "Partly Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue - Full payment not made as of due date."


class Invoice(models.Model):
    """
    An Invoice is a proof of sale that shows details of
    items/services sold to a client and the amount paid/due.

    When an invoice is sent to a client, the Amount Due
    is credited to the 'Accounts Receivable' account book.
    This amount is updated as payment is made on the invoice.
    """

    is_draft = models.BooleanField(default=True)

    # This is a unique invoice number e.g INV-000012,
    NUMBER_PREFIX = "INV"
    number = models.CharField(max_length=16, unique=True, default=get_invoice_next_number)

    client = models.ForeignKey("client.Client", related_name="invoices", on_delete=models.PROTECT)
    issued_date = models.DateField(default=date.today)
    due_date = models.DateField(blank=True, null=True)
    salesperson = models.ForeignKey(
        "user.User",
        related_name="invoices",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # If discount_as_percent is True, discount_value
    # is used in calculation as a percentage
    discount_as_percent = models.BooleanField(blank=True, null=True)
    discount_value = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)

    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = InvoiceManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.client.display_name + "/" + self.number

    def __ini__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # we keep a cached copy of invoice lines as we
        # refer to them often within a request cycle
        self._lines = None

    @property
    def is_sent(self):
        return self.status == InvoiceStatus.SENT

    @property
    def is_overdue(self):
        return self.due_date and date.today() > self.due_date and not self.is_draft

    @property
    def total_incl_tax(self):
        total = 0
        for line in self.all_lines():
            total += line.total_incl_tax
        return total

    @property
    def total_excl_tax(self):
        total = 0
        for line in self.all_lines():
            total += line.total_excl_tax
        return total

    @property
    def total_items(self):
        return self.all_lines().count()

    @property
    def taxes_total(self):
        total = 0
        for line in self.all_lines():
            total += line.taxes_total
        return total

    @property
    def amount_paid(self):
        return sum([payment.amount for payment in self.payments.all()])

    @property
    def amount_due(self):
        return self.total_incl_tax - self.amount_paid

    @property
    def status(self):
        if self.amount_due == 0:
            return InvoiceStatus.PAID
        elif self.is_overdue:
            return InvoiceStatus.OVERDUE
        elif self.amount_paid > 0:
            return InvoiceStatus.PARTLY_PAID
        elif self.is_draft:
            return InvoiceStatus.DRAFT
        else:
            return InvoiceStatus.SENT

    def move_to_draft(self):
        if self.status != InvoiceStatus.SENT:
            return ValidationError("This Invoice cannot be moved to draft.")
        self.is_draft = True
        self.save()
        apps.get_model("accounting.transaction").objects.delete_resource(self)

    move_to_draft.alters_data = True

    def mark_as_sent(self):
        if self.status != InvoiceStatus.DRAFT:
            return ValidationError("This Invoice cannot be marked as sent.")
        self.is_draft = False
        self.save()
        apps.get_model("accounting.transaction").objects.record_invoice(self)

    mark_as_sent.alters_data = True

    def all_lines(self):
        if getattr(self, "_lines", None) is None:
            self._lines = self.lines.prefetch_related("taxes")
        return self._lines

    def generate_each_tax_total(self):
        total = {}
        for line in self.all_lines():
            for tax in line.taxes.all():
                if tax.name in total:
                    total[tax.name] += (tax.rate / 100) * line.total_excl_tax
                else:
                    total[tax.name] = (tax.rate / 100) * line.total_excl_tax
        return total


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        "invoice.Invoice",
        related_name="lines",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey("item.Item", on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    taxes = models.ManyToManyField("tax.Tax", blank=True)

    # this determines how the lines should be
    # arranged on the invoice document.
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.invoice.number} / {self.item.name} / {self.quantity}"

    @property
    def taxes_total(self):
        total = 0
        for tax in self.taxes.all():
            total += (tax.rate / 100) * self.total_excl_tax
        return total

    @property
    def total_excl_tax(self):
        return self.rate * self.quantity

    @property
    def total_incl_tax(self):
        return self.taxes_total + self.total_excl_tax


class PaymentReceived(models.Model):
    invoice = models.ForeignKey(
        "invoice.Invoice", related_name="payments", null=True, on_delete=models.CASCADE
    )
    date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=32)
    description = models.TextField(blank=True)

    objects = PaymentReceivedManager()

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return str(self.amount) + "/" + str(self.invoice.number)
