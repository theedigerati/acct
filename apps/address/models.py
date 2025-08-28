from django.db import models
from acct.abstract_models import AbstractAddress


class Address(AbstractAddress):
    phone_number = models.CharField(max_length=16, blank=True)
