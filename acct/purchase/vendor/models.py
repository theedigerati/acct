from django.db import models


class Vendor(models.Model):
    full_name = models.CharField(max_length=100, blank=True)
    business_name = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    shipping_address = models.ForeignKey(
        "address.Address", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self) -> str:
        return self.display_name
