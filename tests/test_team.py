import pytest
from django.urls import reverse
from apps.team.models import Team


@pytest.mark.django_db
def test_create_list_team(client, test_user, team_data):
    url = reverse("team-list")
    # no permissions
    res = client.post(url, team_data)
    assert res.status_code == 403

    # any authenticated user can get all teams.
    res = client.get(url)
    assert res.status_code == 200
    assert len(res.data) == Team.objects.all().count()

    # team. head cannot create new team.
    test_user.add_permissions("custom_change_team_as_head")
    res = client.post(url, team_data)
    assert res.status_code == 403

    test_user.add_permissions("add_team")
    # create
    res = client.post(url, team_data)
    assert res.status_code == 201
    assert res.data["name"] == team_data["name"]


@pytest.mark.django_db
def test_retrieve_update_delete_team(
    client,
    test_user,
    team_object,
    team_data,
    team_data_partial,
):
    url = reverse("team-detail", kwargs={"pk": team_object.pk})
    # any authenticated user can retrieve team.
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["name"] == team_object.name

    # no permissions
    res = client.put(url, team_data)
    assert res.status_code == 403
    res = client.patch(url, team_data_partial)
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    # team. heads can update team details but cannot delete
    team_object.heads.add(test_user)
    team_object.save()
    res = client.put(url, team_data)
    assert res.status_code == 200
    res = client.patch(url, team_data_partial)
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 403

    # to test mgt. user access permission,
    # we remove test_user from heads
    team_object.heads.remove(test_user)
    team_object.save()
    test_user.add_permissions("change_team", "delete_team")
    res = client.put(url, team_data)
    assert res.status_code == 200
    res = client.patch(url, team_data_partial)
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_update_team_permissions(client, test_user, team_data, team_object, team_data_partial):
    url = reverse("team-detail", kwargs={"pk": team_object.pk})

    # team. heads cannot update team. permissions
    team_object.heads.add(test_user)
    team_object.save()
    team_data["permissions"] = [1, 2, 3]
    team_data_partial["permissions"] = [12, 13, 14]

    res = client.put(url, team_data)
    assert res.status_code == 403
    res = client.patch(url, team_data_partial)
    assert res.status_code == 403

    # but mgt. users can
    team_object.heads.remove(test_user)
    team_object.save()
    test_user.add_permissions("change_team")
    res = client.put(url, team_data)
    assert res.status_code == 200
    assert set(team_object.permissions.values_list("id", flat=True)) == set(
        team_data["permissions"]
    )
    res = client.patch(url, team_data_partial)
    assert res.status_code == 200
    assert set(team_object.permissions.values_list("id", flat=True)) == set(
        team_data_partial["permissions"]
    )


@pytest.mark.django_db
def test_update_team_members(client, test_user, create_tenant_user, team_object):
    user = create_tenant_user("team.member3@localhost")
    add_member_url = reverse("team-add-members", kwargs={"pk": team_object.pk})
    remove_member_url = reverse("team-remove-members", kwargs={"pk": team_object.pk})

    # no permissions
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 403
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 403

    # team. heads
    team_object.heads.add(test_user)
    team_object.save()
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert team_object.user_set.filter(profile__id=user.id).exists()
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert team_object.user_set.filter(profile__id=user.id).exists() is False

    # mgt. users
    team_object.heads.remove(test_user)
    team_object.save()
    test_user.add_permissions("add_team")
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert team_object.user_set.filter(profile__id=user.id).exists()
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert team_object.user_set.filter(profile__id=user.id).exists() is False


@pytest.mark.django_db
def test_list_team_permissions(client, test_user, team_object):
    url = reverse("team-all-permissions", kwargs={"pk": team_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403

    # team. heads
    team_object.heads.add(test_user)
    team_object.save()
    res = client.get(url)
    assert res.status_code == 200

    # mgt. users
    team_object.heads.remove(test_user)
    team_object.save()
    test_user.add_permissions("view_team")
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_list_non_memeber(client, test_user, team_object):
    url = reverse("team-non-members", kwargs={"pk": team_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403

    # team. heads
    team_object.heads.add(test_user)
    team_object.save()
    res = client.get(url)
    assert res.status_code == 200

    # mgt. users
    team_object.heads.remove(test_user)
    team_object.save()
    test_user.add_permissions("view_team")
    res = client.get(url)
    assert res.status_code == 200
