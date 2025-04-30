from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from tenant_users.tenants.models import UserProfile


class User(UserProfile):
    """
    The major user model for access & auth

    The are 4 major user access types (role):
    - Employee user. Regular staff of the org. with basic access.
    - Manager user. Has access to every module on the org. except
      restricted for admin access
    - Admin user. Has all manager access with special administrative
      specifications.
    - Owner user. Has all access. Is django superuser.

    All users can belong to multiple organisations.
    """

    OWNER, ADMIN, MANAGER, EMPLOYEE = "owner", "admin", "manager", "employee"
    ROLE_CHOICES = (
        (OWNER, _("Owner user role")),
        (ADMIN, _("Admin user role")),
        (MANAGER, _("Manager user role")),
        (EMPLOYEE, _("Employee user role")),
    )

    role = models.CharField(
        _("User access role"), max_length=10, choices=ROLE_CHOICES, default=EMPLOYEE
    )
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    designation = models.CharField(max_length=100, default="associate")

    def __str__(self):
        return self.full_name or self.email

    def save(self, *args, **kwargs):
        if not self._state.adding:
            # when updating user role, assign the perms
            # that belong to the new role
            user_in_db = User.objects.get(id=self.id)
            if self.role != user_in_db.role:
                self.assign_default_permissions()

        return super().save(*args, **kwargs)

    @property
    def is_employee(self) -> bool:
        return self.role == self.EMPLOYEE

    @property
    def is_manager(self) -> bool:
        return self.role == self.MANAGER

    @property
    def is_admin(self) -> bool:
        return self.role == self.ADMIN

    @property
    def is_owner(self) -> bool:
        return self.role == self.OWNER

    @property
    def is_manager_or_more(self) -> bool:
        return self.role == self.MANAGER or self.role == self.ADMIN or self.role == self.OWNER

    @property
    def is_admin_or_more(self) -> bool:
        return self.role == self.ADMIN or self.role == self.OWNER

    @property
    def full_name(self) -> str:
        return (
            self.first_name + (" " if self.first_name and self.last_name else "") + self.last_name
        )

    def assign_default_permissions(self):
        perms = self.get_role_default_permissions(self.role)
        self.tenant_perms.user_permissions.add(*perms)

    def get_role_default_permissions(self, _role=None):
        perms = Permission.objects.filter(id__in=[])
        role = _role or self.role
        if role == self.OWNER:
            perms = Permission.objects.all()
        if role == self.ADMIN:
            restrictions = settings.ADMIN_USER_RESTRICTIONS
            perms = Permission.objects.exclude(codename__in=restrictions)
        if role == self.MANAGER:
            restrictions = settings.MANAGER_USER_RESTRICTIONS
            perms = Permission.objects.exclude(codename__in=restrictions)

        return perms

    def add_permissions(self, *perms):
        permissions = Permission.objects.filter(codename__in=list(perms))
        self.tenant_perms.user_permissions.add(*permissions)
