import pytest
from mixer.backend.django import mixer
from django_tenants.utils import tenant_context


@pytest.fixture()
def team_object(test_tenant):
    """
    Team object created with mixer.
    """
    with tenant_context(test_tenant):
        return mixer.blend("team.Team", heads=[])


@pytest.fixture()
def team_data(create_tenant_user, test_tenant, test_user, team_object):
    """
    Sample team data.
    Permissions are the same with 'team_object' permissions because
    mgt. user access is required to change a team's permissions.
    """
    user = create_tenant_user("team.member2@localhost")
    with tenant_context(test_tenant):
        team_object.user_set.add(user.tenant_perms)
    return {
        "name": "accounting",
        "description": "All organisation accountants",
        "permissions": [perm.id for perm in team_object.permissions.all()],
        "heads": [user.id, test_user.id],
    }


@pytest.fixture()
def team_data_partial():
    return {"name": "management", "description": "All management users"}
