import pytest
from django.urls import reverse
from tenant_users.tenants.models import get_public_schema_name
from apps.organisation.models import Organisation
from apps.user.models import User


@pytest.mark.django_db(transaction=True)
def test_list_create_organisation(client, celery_app, celery_worker, test_user, organisation_data):
    url = reverse("organisation-list")
    # no permissions
    res = client.post(url, data=organisation_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403
    # create
    test_user.add_permissions("add_organisation", "view_organisation")
    res = client.post(url, data=organisation_data, format="json")
    assert res.status_code == 201
    assert res.data["address"]["line1"] == organisation_data["address"]["line1"]
    org_id = res.data["id"]
    tenant = Organisation.objects.get(pk=org_id).tenant
    assert tenant.schema_name == get_public_schema_name()  # tenant is intiallly public

    # check tenancy setup task status
    task_id = res.data["task_id"]
    status_url = reverse("organisation-task-status", kwargs={"pk": res.data["id"]})
    res = client.get(status_url)
    assert res.status_code == 200
    task_result = res.data
    assert task_result["id"] == task_id
    assert task_result["status"] == "PENDING"
    while task_result["status"] == "PENDING":
        task_result = client.get(status_url).data
    assert task_result["id"] == task_id
    assert task_result["status"] == "SUCCESS"

    # org tenant should exist now
    tenant = Organisation.objects.get(pk=org_id).tenant
    assert tenant.name == organisation_data["name"]
    assert tenant.user_set.filter(id=test_user.id).exists()  # request user added to org

    # list without permission
    res = client.get(url)
    assert res.status_code == 403
    # list with permission
    test_user.add_permissions("custom_view_all_organisations")
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_retrieve_update_delete_organisation(
    client, test_user, organisation_data, organisation_object
):
    url = reverse("organisation-detail", kwargs={"pk": organisation_object.pk})
    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, data=organisation_data, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_organisation", "change_organisation", "delete_organisation")
    # retrieve
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["name"] == organisation_object.tenant.name
    # update
    res = client.put(url, data=organisation_data, format="json")
    assert res.status_code == 200
    assert res.data["name"] == organisation_data["name"]
    assert res.data["address"]["line1"] == organisation_data["address"]["line1"]
    org_object = Organisation.objects.select_related("tenant").get(pk=res.data["id"])
    assert org_object.tenant.name == organisation_data["name"]  # tenant name should be updated
    assert org_object.tenant.slug == org_object.get_tenant_slug()  # tenant slug should be updated
    # delete
    res = client.delete(url)
    assert res.status_code == 204
    assert Organisation.objects.filter(id=organisation_object.id).exists() is False


@pytest.mark.django_db
def test_organisation_add_users(
    client,
    test_user,
    org_added_users,
    org_users_data,
    users_without_org,
):
    url = reverse("organisation-add-users")
    # no permissions
    res = client.post(url, data=org_users_data, format="json")
    assert res.status_code == 403

    test_user.add_permissions("custom_update_users")
    res = client.post(url, data=org_users_data, format="json")
    assert res.status_code == 200
    assert res.data["added"] == len(users_without_org)  # added users
    assert res.data["exist"] == len(org_added_users)  # users that already existed

    # test that neccessary permissions were assigned to the user
    user = User.objects.get(email=users_without_org[0].email)
    assert len(user.get_all_permissions()) == len(user.get_role_default_permissions())


@pytest.mark.django_db
def test_organisation_remove_users(
    client, test_user, org_added_users, org_users_data, users_without_org
):
    url = reverse("organisation-remove-users")
    # no permissions
    res = client.post(url, data=org_users_data, format="json")
    assert res.status_code == 403

    test_user.add_permissions("custom_update_users")
    res = client.post(url, data=org_users_data)
    assert res.status_code == 200
    assert res.data["removed"] == len(org_added_users)  # removed users
    assert res.data["nonexistent"] == len(users_without_org)  # users not in org
