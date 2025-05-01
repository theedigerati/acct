import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_list_tax(client, test_user, tax_data):
    url = reverse("tax-list")
    # no permissions
    res = client.post(url, tax_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_tax", "view_tax")
    res = client.post(url, tax_data, format="json")
    assert res.status_code == 201
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_retrieve_update_delete_tax(
    client,
    test_user,
    tax_object,
    tax_data,
):
    url = reverse("tax-detail", kwargs={"pk": tax_object.pk})

    # no permissions
    res = client.put(url, tax_data, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_tax", "change_tax", "delete_tax")
    res = client.get(url)
    assert res.status_code == 200
    res = client.put(url, tax_data, format="json")
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db()
def test_bulk_create_or_update_tax(client, test_user, tax_bulk_data):
    url = reverse("tax-bulk-create-or-update")
    test_user.add_permissions("add_tax", "change_tax")
    res = client.post(url, tax_bulk_data, format="json")
    assert res.status_code == 201
    assert len(res.data) == len(tax_bulk_data)
