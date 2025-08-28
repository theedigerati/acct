from django.db import models
from django.utils.translation import gettext_lazy as _


class AbstractAddress(models.Model):
    line1 = models.CharField(_("First line of address"), max_length=255)
    line2 = models.CharField(_("Second line of address"), max_length=255, blank=True)
    city = models.CharField(_("City"), max_length=255)
    state = models.CharField(_("State/County"), max_length=255)
    postcode = models.CharField(_("Post/Zip-code"), max_length=64)
    country = models.CharField(_("Country"), max_length=64)

    class Meta:
        abstract = True
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def __str__(self):
        return self.summary()

    def summary(self):
        return f"{self.line1} {self.state}, {self.country}"

    def to_dict(self):
        return {
            "line1": self.line1,
            "line2": self.line2,
            "city": self.city,
            "state": self.state,
            "postcode": self.postcode,
            "country": self.country,
        }
