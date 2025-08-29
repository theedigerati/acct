from django.db import models
from django.utils.translation import gettext_lazy as _


class Tax(models.Model):
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=100, unique=True)
    number = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = _("Taxes")

    def __str__(self) -> str:
        return f"{self.name} ({self.rate}%)"

    def to_dict(self):
        return {
            "id": self.id,
            "rate": self.rate,
            "name": self.name,
            "number": self.number,
        }
