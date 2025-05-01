import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_crud_client(
    client, test_user, client_object, client_data, client_data_partial
):
    url = reverse("client-list")
    # no permissions
    res = client.post(url, client_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_client", "view_client")
    res = client.post(url, client_data, format="json")
    assert res.status_code == 201
    assert (
        res.data["shipping_address"]["line1"]
        == client_data["shipping_address"]["line1"]
    )
    res = client.get(url)
    assert res.status_code == 200

    url = reverse("client-detail", kwargs={"pk": client_object.pk})
    # no permissions
    res = client.put(url, client_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, client_data_partial, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_client", "change_client", "delete_client")
    res = client.get(url)
    assert res.status_code == 200
    res = client.put(url, client_data, format="json")
    assert res.status_code == 200
    assert (
        res.data["shipping_address"]["line1"]
        == client_data["shipping_address"]["line1"]
    )
    res = client.patch(url, client_data_partial, format="json")
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204
