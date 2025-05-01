import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_crud_vendor(
    client, test_user, vendor_object, vendor_data, vendor_data_partial
):
    url = reverse("vendor-list")
    # no permissions
    res = client.post(url, vendor_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_vendor", "view_vendor")
    res = client.post(url, vendor_data, format="json")
    assert res.status_code == 201
    assert (
        res.data["shipping_address"]["line1"]
        == vendor_data["shipping_address"]["line1"]
    )
    res = client.get(url)
    assert res.status_code == 200

    url = reverse("vendor-detail", kwargs={"pk": vendor_object.pk})
    # no permissions
    res = client.put(url, vendor_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, vendor_data_partial, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_vendor", "change_vendor", "delete_vendor")
    res = client.get(url)
    assert res.status_code == 200
    res = client.put(url, vendor_data, format="json")
    assert res.status_code == 200
    assert (
        res.data["shipping_address"]["line1"]
        == vendor_data["shipping_address"]["line1"]
    )
    res = client.patch(url, vendor_data_partial, format="json")
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204
