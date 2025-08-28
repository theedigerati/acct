from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError

from acct.utils import get_next_number
from .managers import ActiveAccountManager, TransactionManager


def get_journal_next_number():
    return get_next_number(JournalEntry, JournalEntry.NUMBER_PREFIX)


class AccountType(models.TextChoices):
    ASSET = (
        "asset",
        "Asset",
    )
    LIABILITY = (
        "liability",
        "Liability",
    )
    EQUITY = (
        "equity",
        "Equity",
    )
    INCOME = (
        "income",
        "Income",
    )
    EXPENSE = "expense", "Expense"


class AccountSubType(models.Model):
    """
    Account subtypes give more specificity to account types.
    e.g Cash & Bank -> Asset, Current Liability -> Liability etc.
    """

    name = models.CharField(max_length=64, unique=True)
    type = models.CharField(max_length=10, choices=AccountType.choices)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.name


class Account(models.Model):
    """
    Financial Account for recording transactions.
    Each instance must be of one AccountSubType.
    """

    name = models.CharField(max_length=128, db_index=True)
    code = models.CharField(max_length=16, unique=True)
    description = models.TextField(blank=True)
    sub_type = models.ForeignKey(AccountSubType, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="sub_accounts",
    )
    order = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    actives = ActiveAccountManager()

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def type(self) -> str:
        return self.sub_type.type

    @property
    def is_sub_account(self) -> bool:
        return bool(self.parent)

    @property
    def sibling_sub_types(self):
        """
        Account sub types with same type
        """

        return AccountSubType.objects.filter(type=self.type)

    @property
    def sibling_accounts(self):
        """
        Accounts with same sub types
        """
        return Account.objects.filter(sub_type=self.sub_type).exclude(id=self.id)


class TransactionType(models.TextChoices):
    DEBIT = (
        "debit",
        "Debit - Increase Assets & Expense, Decrease Equity, Liability & Income",
    )
    CREDIT = (
        "credit",
        "Credit - Decrease Assets & Expense, Increase Equity, Liability & Income",
    )


class Transaction(models.Model):
    # non-nullable reference for a transaction
    # (invoice | bill | expense | payments | journal entry)
    ref_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    ref_id = models.PositiveIntegerField()
    ref = GenericForeignKey("ref_type", "ref_id")

    name = models.CharField(max_length=50)
    note = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(
        "accounting.Account", related_name="transactions", on_delete=models.PROTECT
    )
    type = models.CharField(max_length=6, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    objects = TransactionManager()

    class Meta:
        indexes = [models.Index(fields=["ref_type", "ref_id", "date"])]
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.account}/{self.name} --> {self.amount}"


class JournalEntry(models.Model):
    name = models.CharField(max_length=50)
    note = models.TextField()
    date = models.DateField(auto_now_add=True)

    # This is a unique journal number e.g JNL-00012,
    NUMBER_PREFIX = "JNL"
    number = models.CharField(max_length=16, unique=True, default=get_journal_next_number)

    is_draft = models.BooleanField(default=True)
    created_by = models.ForeignKey("user.User", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.name

    @property
    def amount(self):
        total_debit = 0
        total_credit = 0
        for line in self.lines.all():
            if line.type == TransactionType.DEBIT:
                total_debit += abs(line.amount)
            else:
                total_credit += abs(line.amount)
        assert total_debit == total_credit
        return total_debit

    def mark_as_published(self):
        if not self.is_draft:
            return ValidationError("Journal Entry is already published!")
        self.is_draft = False
        self.save()
        Transaction.objects.record_journal_entry(self)


class JournalEntryLine(models.Model):
    journal = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    type = models.CharField(max_length=6, choices=TransactionType.choices)

    def __str__(self) -> str:
        return super().__str__()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            return super().save(*args, **kwargs)
        if self.type is TransactionType.DEBIT and self.account.sub_type.type not in [
            AccountType.ASSET,
            AccountType.EXPENSE,
        ]:
            self.amount = -(self.amount)
        if self.type is TransactionType.CREDIT and self.account.sub_type.type in [
            AccountType.ASSET,
            AccountType.EXPENSE,
        ]:
            self.amount = -(self.amount)
        return super().save(*args, **kwargs)
