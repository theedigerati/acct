from datetime import date
from django.db import models


class ExpenseManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("vendor", "account", "paid_through")
            .prefetch_related("taxes")
        )


class Expense(models.Model):
    vendor = models.ForeignKey("vendor.Vendor", null=True, on_delete=models.SET_NULL)
    account = models.ForeignKey("accounting.Account", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    taxes = models.ManyToManyField("tax.Tax", blank=True)
    tax_inclusive = models.BooleanField(default=False)
    paid_through = models.ForeignKey(
        "accounting.Account",
        related_name="expenses_paid_through",
        on_delete=models.CASCADE,
    )
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ExpenseManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.vendor.display_name}: {self.amount}"

    @property
    def amount_incl_tax(self):
        return self.amount if self.tax_inclusive else self.amount + self.taxes_total

    @property
    def amount_excl_tax(self):
        return self.amount - self.taxes_total if self.tax_inclusive else self.amount

    @property
    def taxes_total(self):
        total = 0
        for tax in self.taxes.all():
            total += self.tax_amount(tax.rate)
        return total

    def tax_amount(self, rate):
        if self.tax_inclusive:
            tax_rate = 1 + (rate / 100)
            return round(self.amount - (self.amount / tax_rate), 2)
        else:
            tax_rate = rate / 100
            return round(self.amount * tax_rate, 2)
