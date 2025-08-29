from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VendorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "vendor"
    name = "apps.purchase.vendor"
    verbose_name = _("Vendor")
