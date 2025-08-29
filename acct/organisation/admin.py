from django.contrib import admin
from .models import Tenant, OrgAddress, Organisation, Domain

admin.site.register(Tenant)
admin.site.register(OrgAddress)
admin.site.register(Organisation)
admin.site.register(Domain)
