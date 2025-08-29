from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExpenseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "expense"
    name = "apps.purchase.expense"
    verbose_name = _("Expense")
