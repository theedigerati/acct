import pytest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from apps.accounting.models import Transaction


@pytest.mark.django_db
def test_create_list_expense(client, test_user, expense_object, expense_data):
    url = reverse("expense-list")
    # no permissions
    res = client.post(url, expense_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_expense", "view_expense")
    # create
    res = client.post(url, expense_data, format="json")
    assert res.status_code == 201
    # test transaction
    contenttype = ContentType.objects.get(app_label="expense", model="expense")
    assert Transaction.objects.filter(
        ref_type=contenttype, ref_id=res.data["id"]
    ).count() == (2 + len(expense_data["taxes"]))
    # list
    res = client.get(url)
    assert res.status_code == 200

    url = reverse("expense-detail", kwargs={"pk": expense_object.pk})
    # no permissions
    res = client.put(url, expense_data, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_expense", "change_expense", "delete_expense")
    res = client.get(url)
    assert res.status_code == 200
    res = client.put(url, expense_data, format="json")
    assert res.status_code == 200
    res = client.delete(url)
    assert res.status_code == 204
