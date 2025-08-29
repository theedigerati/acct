from django.contrib import admin

# from django.contrib.auth.models import Permission
# from django.contrib.contenttypes.models import ContentType
from tenant_users.permissions.models import UserTenantPermissions
from .models import User

admin.site.register(User)
admin.site.register(UserTenantPermissions)
# admin.site.register(Permission)
# admin.site.register(ContentType)
