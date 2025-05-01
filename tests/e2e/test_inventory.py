import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_create_list_item(client, test_user, item_data):
    url = reverse("item-list")
    # no permissions
    res = client.post(url, item_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_item", "view_item")
    res = client.post(url, item_data, format="json")
    assert res.status_code == 201
    assert res.data["type"] == item_data["type"]
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_retrieve_update_delete_item(
    client, test_user, item_object, item_data, item_data_partial
):
    url = reverse("item-detail", kwargs={"pk": item_object.pk})

    # no permissions
    res = client.put(url, item_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, item_data_partial, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_item", "change_item", "delete_item")
    res = client.get(url)
    assert res.status_code == 200
    res = client.put(url, item_data, format="json")
    assert res.status_code == 200
    assert res.data["name"] == item_data["name"]
    res = client.patch(url, item_data_partial, format="json")
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204
