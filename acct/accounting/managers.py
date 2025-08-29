from datetime import datetime, timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.db import transaction
from django.utils import timezone as django_timezone
from django.apps import apps
from django.conf import settings
from apps.purchase.bill.models import Bill, PaymentMade
from apps.purchase.expense.models import Expense
from apps.sales.invoice.models import Invoice, PaymentReceived


class ActiveAccountManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class TransactionManager(models.Manager):
    """
    Custon manager methods to record & delete
    transactions from resources.

    Note: Debit transactions increase Asset & Expense accounts,
          decrease liability, equity & income accounts.

          Credit transactions decrease Asset & Expense accounts,
          increase liability, equity & income accounts.
    """

    def record_invoice(self, invoice):
        assert isinstance(invoice, Invoice)
        transaction_data = {
            "date": invoice.issued_date,
            "ref": invoice,
            "name": f"Invoice {invoice.number}",
            "note": "Invoice",
            "transactions": [
                {
                    "account_code": "1200",
                    "type": "debit",
                    "amount": invoice.total_incl_tax,
                },
                {
                    "account_code": "4000-3",
                    "type": "credit",
                    "amount": invoice.total_excl_tax,
                },
                *[
                    {
                        "name": f"{tax_name} for Invoice {invoice.number}",
                        "account_code": "2005-1",
                        "type": "credit",
                        "amount": tax_amount,
                    }
                    for tax_name, tax_amount in invoice.generate_each_tax_total().items()
                ],
            ],
        }
        self._record_transaction(**transaction_data)

    def record_payment_received(self, payment):
        assert isinstance(payment, PaymentReceived)
        transaction_data = {
            "date": payment.date,
            "ref": payment,
            "name": (
                f"Payment for {payment.invoice.number}"
                if payment.invoice
                else "Payment received"
            ),
            "note": (
                payment.description or "Invoice payment"
                if payment.invoice
                else payment.description or "Payment received"
            ),
            "transactions": [
                {
                    "account_code": "1000-1",
                    "type": "debit",
                    "amount": payment.amount,
                },
                {
                    "account_code": "1200",
                    "type": "credit",
                    "amount": -(payment.amount),
                },
            ],
        }
        self._record_transaction(**transaction_data)

    def record_bill(self, bill):
        assert isinstance(bill, Bill)
        transaction_data = {
            "date": bill.bill_date,
            "ref": bill,
            "name": f"Bill {bill.number}",
            "note": "Bill",
            "transactions": [
                {
                    "account_code": "2000",
                    "type": "credit",
                    "amount": bill.total_incl_tax,
                },
                *[
                    {
                        "name": f"{tax_name} for Bill {bill.number}",
                        "account_code": "6016",
                        "type": "debit",
                        "amount": tax_amount,
                    }
                    for tax_name, tax_amount in bill.generate_each_tax_total().items()
                ],
            ],
        }
        self._record_transaction(**transaction_data)

    def record_payment_made(self, payment):
        assert isinstance(payment, PaymentMade)
        transaction_data = {
            "date": payment.date,
            "ref": payment,
            "name": (
                f"Payment for {payment.bill.number}" if payment.bill else "Payment made"
            ),
            "note": (
                payment.description or "Bill payment"
                if payment.bill
                else payment.description or "Payment made"
            ),
            "transactions": [
                {
                    "account_code": "1000-1",
                    "type": "credit",
                    "amount": -(payment.amount),
                },
                {
                    "account_code": "2000",
                    "type": "debit",
                    "amount": -(payment.amount),
                },
            ],
        }
        self._record_transaction(**transaction_data)

    def record_expense(self, expense):
        assert isinstance(expense, Expense)
        transaction_data = {
            "date": expense.date,
            "ref": expense,
            "name": f"Expense ({expense.account.name})",
            "note": expense.notes,
            "transactions": [
                {
                    "name": "Expense",
                    "account_code": expense.account.code,
                    "type": "debit",
                    "amount": expense.amount_excl_tax,
                },
                {
                    "account_code": expense.paid_through.code,
                    "type": "credit",
                    "amount": -(expense.amount_incl_tax),
                },
                *[
                    {
                        "name": f"{tax.name} for Expense",
                        "account_code": "6016",
                        "type": "debit",
                        "amount": expense.tax_amount(tax.rate),
                    }
                    for tax in expense.taxes.all()
                ],
            ],
        }
        self._record_transaction(**transaction_data)

    def record_journal_entry(self, journal_entry):
        JournalEntry = apps.get_model("accounting.JournalEntry")
        assert isinstance(journal_entry, JournalEntry)
        transaction_data = {
            "date": journal_entry.date,
            "ref": journal_entry,
            "name": f"Journal Entry: {journal_entry.name}",
            "note": journal_entry.note,
            "transactions": [
                *[
                    {
                        "account_code": line.account.code,
                        "type": line.type,
                        "amount": line.amount,
                    }
                    for line in journal_entry.lines.select_related("account")
                ]
            ],
        }
        self._record_transaction(**transaction_data)

    def delete_resource(self, resource):
        assert isinstance(
            resource, (Invoice, PaymentReceived, Bill, PaymentMade, Expense)
        )
        contenttype = ContentType.objects.get(
            app_label=resource._meta.app_label,
            model=resource._meta.model_name,
        )
        self.get_queryset().filter(ref_type=contenttype, ref_id=resource.id).delete()

    def _record_transaction(self, **kwargs):
        account_model = self.model.account.field.related_model
        queryset = self.get_queryset()
        contenttype = ContentType.objects.get(
            app_label=kwargs["ref"]._meta.app_label,
            model=kwargs["ref"]._meta.model_name,
        )
        defaults = {
            "ref_type": contenttype,
            "ref_id": kwargs["ref"].id,
            "ref": kwargs["ref"],
            "date": datetime.combine(
                kwargs["date"],
                django_timezone.now().time(),
                timezone.utc if settings.USE_TZ else None,
            ),
            "name": kwargs["name"],
            "note": kwargs["note"],
        }

        with transaction.atomic():
            # delete existing records
            queryset.filter(ref_type=contenttype, ref_id=kwargs["ref"].id).delete()
            try:
                for record in kwargs["transactions"]:
                    _defaults = {
                        **defaults,
                        "name": (
                            record["name"] if "name" in record else defaults["name"]
                        ),
                    }
                    queryset.create(
                        account=account_model.actives.get(code=record["account_code"]),
                        type=record["type"],
                        amount=record["amount"],
                        **_defaults,
                    )
            except MultipleObjectsReturned:
                raise ValidationError(
                    "Multiple transactions/accounts found with the same reference."
                )
            except account_model.DoesNotExist:
                raise ValidationError("Account provided was not found or is archived.")
