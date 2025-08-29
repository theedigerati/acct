from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrganisationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "organisation"
    name = "apps.organisation"
    verbose_name = _("Organisation")
