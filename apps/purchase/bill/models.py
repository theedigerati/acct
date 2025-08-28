from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
from django.apps import apps
from apps.purchase.bill.managers import BillManager, PaymentMadeManager
from acct.utils import get_next_number


def get_bill_next_number():
    return get_next_number(Bill, Bill.NUMBER_PREFIX)


class BillStatus(models.TextChoices):
    DRAFT = "draft", "Draft - Generated but not sent to the client."
    OPEN = "open", "Open"
    PARTLY_PAID = "partly paid", "Partly Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue - Full payment not made as of due date."


class Bill(models.Model):
    """
    A Bill is a proof of purchase sent by a vendor/supplier that
    shows details of items/services purchased and the amount paid.

    When a Bill is not a draft the amount due on the Bill is credited
    to the 'Acoounts Payable' account book. This amount is updated as
    payment is made on the bill.
    """

    is_draft = models.BooleanField(default=True)

    # This is the bill number e.g B-00012,
    # generated on the frontend.
    NUMBER_PREFIX = "B"
    number = models.CharField(max_length=16, unique=True, default=get_bill_next_number)

    vendor = models.ForeignKey("vendor.Vendor", related_name="bills", on_delete=models.PROTECT)
    bill_date = models.DateField(default=date.today)
    due_date = models.DateField(blank=True, null=True)

    # If discount_as_percent is True, discount_value
    # is used in calculation as a percentage
    discount_as_percent = models.BooleanField(blank=True, null=True)
    discount_value = models.DecimalField(decimal_places=2, max_digits=10, blank=True, null=True)

    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = BillManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.vendor.display_name + "/" + self.number

    def __ini__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # we keep a cached copy of bill lines as we
        # refer to them often within a request cycle
        self._lines = None

    @property
    def is_open(self):
        return self.status == BillStatus.OPEN

    @property
    def total_items(self):
        return self.all_lines().count()

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
    def is_overdue(self):
        return self.due_date and date.today() > self.due_date and not self.is_draft

    @property
    def status(self):
        is_overdue = self.due_date and date.today() > self.due_date
        if self.amount_due == 0:
            return BillStatus.PAID
        elif is_overdue and not self.is_draft:
            return BillStatus.OVERDUE
        elif self.amount_paid > 0:
            return BillStatus.PARTLY_PAID
        elif self.is_draft:
            return BillStatus.DRAFT
        else:
            return BillStatus.OPEN

    def move_to_draft(self):
        if self.status != BillStatus.OPEN:
            return ValidationError("This Bill cannot be moved to draft.")
        self.is_draft = True
        self.save()
        apps.get_model("accounting.transaction").objects.delete_resource(self)

    move_to_draft.alters_data = True

    def mark_as_open(self):
        if self.status != BillStatus.DRAFT:
            return ValidationError("This Bill cannot be marked as open.")
        self.is_draft = False
        self.save()
        apps.get_model("accounting.transaction").objects.record_bill(self)

    mark_as_open.alters_data = True

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


class BillLine(models.Model):
    bill = models.ForeignKey(
        "bill.Bill",
        related_name="lines",
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey("item.Item", blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    rate = models.DecimalField(max_digits=12, decimal_places=2)
    taxes = models.ManyToManyField("tax.Tax", blank=True)

    # this determines how the lines should be
    # arranged on the bill document.
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.bill.number} / {self.name} / {self.quantity}"

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


class PaymentMade(models.Model):
    bill = models.ForeignKey(
        "bill.Bill", related_name="payments", null=True, on_delete=models.CASCADE
    )
    date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=32)
    description = models.TextField(blank=True)

    objects = PaymentMadeManager()

    def __str__(self) -> str:
        return str(self.amount) + "/" + str(self.bill.number)
