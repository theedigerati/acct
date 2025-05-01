import contextlib
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from tenant_users.tenants.models import (
    TenantBase,
    ExistsError,
    DeleteError,
    get_public_schema_name,
)
from django_tenants.models import DomainMixin
from apps.accounting.factory import AccountingFactory
from apps.user.models import User
from core.abstract_models import AbstractAddress


class Tenant(TenantBase):
    name = models.CharField(max_length=100)


class OrgAddress(AbstractAddress):
    class Meta:
        default_permissions = []


class Organisation(models.Model):
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, default="HQ")
    description = models.TextField(max_length=255, blank=True)
    address = models.ForeignKey(
        "organisation.OrgAddress",
        related_name="organisations",
        on_delete=models.SET_NULL,
        null=True,
    )
    phone = models.CharField(max_length=15, blank=True)
    tenant = models.OneToOneField(
        "organisation.Tenant", related_name="organisation", on_delete=models.CASCADE
    )

    # celery task id for tenancy setup
    task_id = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("name", "branch")
        permissions = [
            ("custom_update_users", "Can add/remove users"),
            ("custom_view_all_organisations", "Can view all organisations"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self._state.adding:
            try:
                self.tenant
            except ObjectDoesNotExist:
                # we'll use the public tenant for now
                # actual tenant will be created in a celery task on the view
                public_tenant = Tenant.objects.get(schema_name=get_public_schema_name())
                self.tenant = public_tenant
        elif self.tenant.schema_name != get_public_schema_name():
            self._update_tenant()

        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.name}, {self.branch}."

    @property
    def tenant_slug(self) -> str:
        return self.tenant.slug

    @property
    def users(self):
        return self.tenant.user_set.count()

    def add_users(self, users: list = [], is_superuser=False):
        res = {"added": 0, "exist": 0}
        for user in users:
            try:
                self.tenant.add_user(user, is_superuser=is_superuser, is_staff=is_superuser)
                user.assign_default_permissions()
                res["added"] += 1
            except ExistsError:
                res["exist"] += 1
        return res

    def remove_users(self, users: list = []):
        res = {"removed": 0, "nonexistent": 0}
        for user in users:
            try:
                self.tenant.remove_user(user)
                res["removed"] += 1
            except ObjectDoesNotExist:
                res["nonexistent"] += 1
            except DeleteError:
                pass
        return res

    def get_tenant_slug(self):
        org_name = self.name.replace(" ", "-").lower()
        org_branch = self.branch.lower()
        return f"{org_name}-{org_branch}"

    def create_tenant(self, request_user_id=None):
        # on a request cycle, this method should be ran async
        # e.g using celery, coz `provision_tenant` will run migrations
        from tenant_users.tenants.tasks import provision_tenant

        tenant_slug = self.get_tenant_slug()
        provision_tenant(
            tenant_name=self.name,
            tenant_slug=tenant_slug,
            user_email=settings.BASE_TENANT_OWNER_EMAIL,
            is_staff=True,
        )
        self.tenant = Tenant.objects.get(slug=tenant_slug)
        if request_user_id:
            user = User.objects.get(id=request_user_id)
            with contextlib.suppress(ExistsError):
                self.tenant.add_user(user)
        self.save()

    def setup_default_accounts(self):
        accounting_factory = AccountingFactory(self.tenant.schema_name)
        accounting_factory.generate_default_accounts()

    def _update_tenant(self):
        tenant_slug = self.get_tenant_slug()
        if self.tenant.slug == tenant_slug:
            return
        Tenant.objects.filter(id=self.tenant.id).update(name=self.name, slug=tenant_slug)
        if hasattr(settings, "TENANT_SUBFOLDER_PREFIX"):
            tenant_domain = tenant_slug
        else:
            tenant_domain = f"{tenant_slug}.{settings.TENANT_USERS_DOMAIN}"
        Domain.objects.filter(tenant=self.tenant).update(domain=tenant_domain)

    def _add_all_owners(self):
        owners = User.objects.filter(role=User.OWNER)
        self.add_users(list(owners), is_superuser=True)


class Domain(DomainMixin):
    pass
