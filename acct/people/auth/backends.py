import jwt
from django.contrib.auth.models import Permission

from acct.graphql.people.dataloaders import UserByEmailLoader
from acct.people.auth.utils import (
    JWT_ACCESS_TYPE,
    JWT_THIRDPARTY_ACCESS_TYPE,
    get_token_from_request,
    is_acct_token,
    jwt_decode,
)
from acct.people.models import User, UserTenantPermissions


class BaseBackend:
    def authenticate(self, request, **kwargs):
        return None

    def get_user(self, user_id):
        return None

    def get_user_permissions(self, user_obj, tenant):
        return set()

    def get_group_permissions(self, user_obj, tenant):
        return set()

    def get_all_permissions(self, user_obj, tenant):
        return {
            *self.get_user_permissions(user_obj, tenant=tenant),
            *self.get_group_permissions(user_obj, tenant=tenant),
        }

    def has_perm(self, user_obj, perm, tenant):
        return perm in self.get_all_permissions(user_obj, tenant=tenant)


class TenantBackend(BaseBackend):
    def _get_user_permissions(self, user_tenant_obj):
        return user_tenant_obj.permissions.all()

    def _get_team_permissions(self, user_tenant_obj):
        return Permission.objects.filter(team__in=user_tenant_obj.user.teams.all())

    def _get_permissions(self, user_obj, tenant, from_name):
        """Return the permissions of `user_obj` in `tenant` from `from_name`.

        `from_name` can be either "team" or "user" to return permissions from
        `_get_team_permissions` or `_get_user_permissions` respectively.
        """
        if not user_obj.is_active or user_obj.is_anonymous or tenant is None:
            return set()

        perm_cache_name = "_%s_perm_cache_%s" % (from_name, str(tenant.pk))
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                user_tenant_obj = UserTenantPermissions(user=user_obj, tenant=tenant)
                perms = getattr(self, "_get_%s_permissions" % from_name)(
                    user_tenant_obj
                )
            perms = perms.values_list("content_type__app_label", "codename").order_by()
            setattr(
                user_obj, perm_cache_name, {"%s.%s" % (ct, name) for ct, name in perms}
            )
        return getattr(user_obj, perm_cache_name)

    def get_user_permissions(self, user_obj, tenant):
        """Return a set of permissions the user `user_obj` holds directly."""
        return self._get_permissions(user_obj, tenant, "user")

    def get_team_permissions(self, user_obj, tenant):
        """Return a set of permissions the user `user_obj` gets from their teams."""
        return self._get_permissions(user_obj, tenant, "team")

    def get_all_permissions(self, user_obj, tenant):
        if not user_obj.is_active or user_obj.is_anonymous or tenant is None:
            return set()
        tenant_perm_cache_name = f"_perm_cache_{tenant.pk}"
        if not hasattr(user_obj, tenant_perm_cache_name):
            all_perms = super().get_all_permissions(user_obj)
            setattr(user_obj, tenant_perm_cache_name, all_perms)
        return user_obj._perm_cache

    def has_perm(self, user_obj, perm, tenant):
        return user_obj.is_active and super().has_perm(user_obj, perm, tenant=tenant)


class JWTBackend(TenantBackend):
    def authenticate(self, request=None, **kwargs):
        return load_user_from_request(request)

    def get_user(self, user_id):
        try:
            return User.objects.get(email=user_id, is_active=True)
        except User.DoesNotExist:
            return None


def load_user_from_request(request):
    if request is None:
        return None
    jwt_token = get_token_from_request(request)
    if not jwt_token or not is_acct_token(jwt_token):
        return None
    payload = jwt_decode(jwt_token)

    jwt_type = payload.get("type")
    if jwt_type not in [JWT_ACCESS_TYPE, JWT_THIRDPARTY_ACCESS_TYPE]:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )

    user = UserByEmailLoader(request).load(payload["email"]).get()
    user_jwt_token = payload.get("token")
    if not user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    if not user:
        raise jwt.InvalidTokenError(
            "Invalid token. User does not exist or is inactive."
        )
    if user.jwt_token_key != user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )

    return user
