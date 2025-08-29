from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ItemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "item"
    name = "apps.inventory.item"
    verbose_name = _("Inventory Item")
