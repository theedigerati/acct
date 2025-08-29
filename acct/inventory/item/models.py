from random import randint
from django.db import models


class ItemType(models.TextChoices):
    GOODS = "goods", "Goods - Physical item"
    SERVICE = "service", "Service - Service offered"


class Item(models.Model):
    type = models.CharField(
        max_length=10, choices=ItemType.choices, default=ItemType.GOODS
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=128, blank=True, unique=True)
    upc = models.CharField(max_length=64, blank=True)
    unit = models.CharField(max_length=10, blank=True)
    sellable = models.BooleanField(default=False)
    track_stock = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    cost_price = models.DecimalField(
        decimal_places=2, max_digits=16, blank=True, null=True
    )
    selling_price = models.DecimalField(
        decimal_places=2, max_digits=16, blank=True, null=True
    )
    stock_on_hand = models.PositiveIntegerField(blank=True, null=True)
    low_stock_threshold = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.sku is None or len(self.sku) < 1:
            self.sku = (
                self.name.replace(" ", "").lower() + "-" + str(randint(1000, 9999))
            )
        super().save(*args, **kwargs)
