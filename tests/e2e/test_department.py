import pytest
from django.urls import reverse
from apps.department.models import Department


@pytest.mark.django_db
def test_create_list_dept(client, test_user, dept_data):
    url = reverse("department-list")
    # no permissions
    res = client.post(url, dept_data)
    assert res.status_code == 403

    # any authenticated user can get all depts.
    res = client.get(url)
    assert res.status_code == 200
    assert len(res.data) == Department.objects.all().count()

    # dept. head cannot create new dept.
    test_user.add_permissions("custom_change_department_as_head")
    res = client.post(url, dept_data)
    assert res.status_code == 403

    test_user.add_permissions("add_department")
    # create
    res = client.post(url, dept_data)
    assert res.status_code == 201
    assert res.data["name"] == dept_data["name"]


@pytest.mark.django_db
def test_retrieve_update_delete_dept(
    client,
    test_user,
    dept_object,
    dept_data,
    dept_data_partial,
):
    url = reverse("department-detail", kwargs={"pk": dept_object.pk})
    # any authenticated user can retrieve dept.
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["name"] == dept_object.name

    # no permissions
    res = client.put(url, dept_data)
    assert res.status_code == 403
    res = client.patch(url, dept_data_partial)
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    # dept. heads can update department details but cannot delete
    dept_object.heads.add(test_user)
    dept_object.save()
    res = client.put(url, dept_data)
    assert res.status_code == 200
    res = client.patch(url, dept_data_partial)
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 403

    # to test mgt. user access permission,
    # we remove test_user from heads
    dept_object.heads.remove(test_user)
    dept_object.save()
    test_user.add_permissions("change_department", "delete_department")
    res = client.put(url, dept_data)
    assert res.status_code == 200
    res = client.patch(url, dept_data_partial)
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_update_dept_permissions(
    client, test_user, dept_data, dept_object, dept_data_partial
):
    url = reverse("department-detail", kwargs={"pk": dept_object.pk})

    # dept. heads cannot update dept. permissions
    dept_object.heads.add(test_user)
    dept_object.save()
    dept_data["permissions"] = [1, 2, 3]
    dept_data_partial["permissions"] = [12, 13, 14]

    res = client.put(url, dept_data)
    assert res.status_code == 403
    res = client.patch(url, dept_data_partial)
    assert res.status_code == 403

    # but mgt. users can
    dept_object.heads.remove(test_user)
    dept_object.save()
    test_user.add_permissions("change_department")
    res = client.put(url, dept_data)
    assert res.status_code == 200
    assert set(dept_object.permissions.values_list("id", flat=True)) == set(
        dept_data["permissions"]
    )
    res = client.patch(url, dept_data_partial)
    assert res.status_code == 200
    assert set(dept_object.permissions.values_list("id", flat=True)) == set(
        dept_data_partial["permissions"]
    )


@pytest.mark.django_db
def test_update_dept_members(client, test_user, create_tenant_user, dept_object):
    user = create_tenant_user("dept.member3@localhost")
    add_member_url = reverse("department-add-members", kwargs={"pk": dept_object.pk})
    remove_member_url = reverse(
        "department-remove-members", kwargs={"pk": dept_object.pk}
    )

    # no permissions
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 403
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 403

    # dept. heads
    dept_object.heads.add(test_user)
    dept_object.save()
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert dept_object.user_set.filter(profile__id=user.id).exists()
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert dept_object.user_set.filter(profile__id=user.id).exists() is False

    # mgt. users
    dept_object.heads.remove(test_user)
    dept_object.save()
    test_user.add_permissions("add_department")
    res = client.post(add_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert dept_object.user_set.filter(profile__id=user.id).exists()
    res = client.post(remove_member_url, {"users": [user.pk]})
    assert res.status_code == 200
    assert dept_object.user_set.filter(profile__id=user.id).exists() is False


@pytest.mark.django_db
def test_list_dept_permissions(client, test_user, dept_object):
    url = reverse("department-all-permissions", kwargs={"pk": dept_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403

    # dept. heads
    dept_object.heads.add(test_user)
    dept_object.save()
    res = client.get(url)
    assert res.status_code == 200

    # mgt. users
    dept_object.heads.remove(test_user)
    dept_object.save()
    test_user.add_permissions("view_department")
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_list_non_memeber(client, test_user, dept_object):
    url = reverse("department-non-members", kwargs={"pk": dept_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403

    # dept. heads
    dept_object.heads.add(test_user)
    dept_object.save()
    res = client.get(url)
    assert res.status_code == 200

    # mgt. users
    dept_object.heads.remove(test_user)
    dept_object.save()
    test_user.add_permissions("view_department")
    res = client.get(url)
    assert res.status_code == 200
