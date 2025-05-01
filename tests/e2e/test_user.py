import pytest
from django.urls import reverse
from django.conf import settings
from apps.user.models import User


@pytest.mark.django_db
def test_create_list_user(client, test_user, user_data):
    """
    Test USER create & list actions.
    """
    url = reverse("user-list")
    # no permissions
    res = client.post(url, data=user_data, format="json")
    assert res.status_code == 403

    # any authenticated user can list users,
    # these users are filtered
    res = client.get(url)
    assert res.status_code == 200

    # create
    test_user.add_permissions("add_user")
    res = client.post(url, user_data, format="json")
    assert res.status_code == 201
    assert res.data["email"] == user_data["email"]


@pytest.mark.django_db
def test_unsafe_create_user(client, test_tenant, test_user, user_data):
    url = reverse("user-unsafe-create")
    test_user.add_permissions("add_user")
    res = client.post(url, user_data, format="json")
    assert res.status_code == 201
    assert res.data["email"] == user_data["email"]
    assert test_tenant.user_set.filter(email=user_data["email"]).exists()


@pytest.mark.django_db
def test_retrieve_user(
    client, test_user, user_object_without_org, user_object_with_org
):
    """
    Test USER retrieve action where they belong to the
    same organisation and where they don't.
    """
    test_user.add_permissions("view_user")
    # different organisation
    url = reverse("user-detail", kwargs={"pk": user_object_without_org.pk})
    res = client.get(url)
    assert res.status_code == 404
    # same organisation
    url = reverse("user-detail", kwargs={"pk": user_object_with_org.pk})
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["email"] == user_object_with_org.email


@pytest.mark.django_db
def test_update_user(
    client,
    test_user,
    user_data,
    user_data_partial,
    user_object_without_org,
    user_object_with_org,
):
    """
    Test USER update action where they belong to the
    same organisation and where they don't.
    """
    url = reverse("user-detail", kwargs={"pk": user_object_without_org.pk})
    # no permissions
    res = client.put(url, user_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, user_data_partial, format="json")
    assert res.status_code == 403

    test_user.add_permissions("change_user")
    # different organisation
    res = client.put(url, user_data, format="json")
    assert res.status_code == 404
    res = client.patch(url, user_data_partial, format="json")
    assert res.status_code == 404
    # same organisation
    url = reverse("user-detail", kwargs={"pk": user_object_with_org.pk})
    res = client.put(url, user_data, format="json")
    assert res.status_code == 200
    assert res.data["last_name"] == user_data["last_name"]
    res = client.patch(url, user_data_partial, format="json")
    assert res.status_code == 200
    assert res.data["last_name"] == user_data_partial["last_name"]


@pytest.mark.django_db
def test_delete_user(client, test_user, user_object_with_org):
    """
    Test USER delete action.
    """
    url = reverse("user-detail", kwargs={"pk": user_object_with_org.pk})
    # no permission
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("delete_user")
    res = client.delete(url)
    assert res.status_code == 204
    assert User.objects.filter(id=user_object_with_org.id).exists() is False


@pytest.mark.django_db
def test_list_user_permissions(client, test_user, user_object_with_org):
    # get permissions for request user
    url = reverse("user-my-permissions")
    res = client.get(url)
    assert res.status_code == 200
    assert len(res.data) == len(test_user.get_all_permissions())

    url = reverse("user-permissions", kwargs={"pk": test_user.pk})
    res = client.get(url)
    assert res.status_code == 200
    assert len(res.data) == len(test_user.get_all_permissions())

    # get permissions for another user
    url = reverse("user-permissions", kwargs={"pk": user_object_with_org.pk})
    res = client.get(url)
    assert res.status_code == 403

    # only mgt. users can
    test_user.role = User.MANAGER
    test_user.save()
    res = client.get(url)
    assert len(res.data) == len(user_object_with_org.get_all_permissions())

    test_user.role = User.ADMIN
    test_user.save()
    res = client.get(url)
    assert len(res.data) == len(user_object_with_org.get_all_permissions())


# TODO: 2 tasks
#
# 1. Implement tests for user hierarchy update for each user type.
# 2. Implement tests for user role hierarchy create and update
#    for each user type.


@pytest.mark.django_db
def test_permissions_source_of_truth(client, test_user, dept_object):
    url = reverse("permission-source-of-truth")

    # no permisions
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("change_user", "change_department")
    res = client.get(url)
    assert res.status_code == 200
    assert res.data.keys() == settings.PERMISSION_CATEGORIES.keys()

    # source of truth for user
    sot_user_url = url + "?user=" + str(test_user.id)
    res = client.get(sot_user_url)
    assert res.status_code == 200
    user_model_permissions = next(
        (
            category_dict["user"]
            for category_dict in res.data.values()
            if "user" in category_dict
        ),
        None,
    )
    assert user_model_permissions
    assert any(
        perm_data["active"]
        for perm_data in user_model_permissions
        if perm_data["perm"]["codename"] == "change_user"
    )

    # source of truth for department
    dept_object.add_permissions("change_invoice")
    sot_dept_url = url + "?department=" + str(dept_object.id)
    res = client.get(sot_dept_url)
    assert res.status_code == 200
    invoice_model_permissions = next(
        (
            category_dict["invoice"]
            for category_dict in res.data.values()
            if "invoice" in category_dict
        ),
        None,
    )
    assert invoice_model_permissions
    assert any(
        perm_data["active"]
        for perm_data in invoice_model_permissions
        if perm_data["perm"]["codename"] == "change_invoice"
    )

    # source of truth for user in department
    dept_object.add_members([test_user])
    res = client.get(sot_user_url)
    invoice_model_permissions = next(
        (
            category_dict["invoice"]
            for category_dict in res.data.values()
            if "invoice" in category_dict
        ),
        None,
    )
    assert any(
        perm_data["active"] and perm_data["inherited"]
        for perm_data in invoice_model_permissions
        if perm_data["perm"]["codename"] == "change_invoice"
    )
