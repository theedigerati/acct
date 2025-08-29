from django.contrib import admin
from apps.accounting.models import Account, AccountSubType, Transaction


admin.site.register(AccountSubType)
admin.site.register(Account)
admin.site.register(Transaction)
