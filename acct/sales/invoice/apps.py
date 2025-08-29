from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InvoiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "invoice"
    name = "apps.sales.invoice"
    verbose_name = _("Invoice")
