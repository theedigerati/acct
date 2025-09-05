from functools import partial
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import (
    BaseUserManager,
    Permission,
    PermissionsMixin,
)
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now


class Tenant(models.Model):
    slug = models.SlugField(blank=True)

    # The owner of the tenant. Only they can delete it. This can be changed,
    # but it can't be blank. There should always be an owner.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False, db_index=True)


class UserManager(BaseUserManager):
    def create_user(
        self, email, password=None, is_staff=False, is_active=True, **extra_fields
    ):
        """Create a user instance with the given email and password."""
        email = self.normalize_email(email)
        # username field might be added by a 3rd-party auth system
        extra_fields.pop("username", None)

        user = self.model(
            email=email, is_active=is_active, is_staff=is_staff, **extra_fields
        )
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        is_staff = extra_fields.setdefault("is_staff", True)
        is_superuser = extra_fields.setdefault("is_superuser", True)

        if is_staff is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if is_superuser is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(default=uuid4, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=True)
    last_confirm_email_request = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_password_reset_request = models.DateTimeField(null=True, blank=True)
    jwt_token_key = models.CharField(
        max_length=12, default=partial(get_random_string, length=12)
    )
    language_code = models.CharField(
        max_length=35, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    teams = models.ManyToManyField("people.Team", blank=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        ordering = ("email",)

    def __str__(self):
        # Override the default __str__ of AbstractUser that returns USERNAME_FIELD,
        # which may  lead to leaking sensitive data in logs.
        return str(self.uuid)

    def get_full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.email

    def get_short_name(self):
        return self.email


class UserTenantPermissions(models.Model):
    user = models.ForeignKey(User, related_name="tenants", on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, related_name="users", on_delete=models.CASCADE)
    permissions = models.ManyToManyField(Permission, blank=True)


class Team(models.Model):
    """A team is a tenant-based group of users.

    Teams can be given specific perimissions similar to a django auth group.
    Additional permissions can be assigned to any members of a team
    to become a Team Admin.

    A team admin can modify the details of a team except its permissions.
    """

    name = models.CharField(max_length=150)
    description = models.CharField(max_length=256, blank=True)
    tenant = models.ForeignKey(Tenant, related_name="teams", on_delete=models.CASCADE)
    admins = models.ManyToManyField(User, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_public = models.BooleanField(default=True)
