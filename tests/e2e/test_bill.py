import pytest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from apps.accounting.models import Transaction
from apps.purchase.bill.models import BillStatus, get_bill_next_number
from mixer.backend.django import mixer


@pytest.mark.django_db
def test_create_list_bill(client, test_user, bill_data):
    url = reverse("bill-list")
    # no permissions
    res = client.post(url, bill_data)
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_bill", "view_bill", "view_transation")
    # create
    next_number = get_bill_next_number()
    res = client.post(url, bill_data, format="json")
    assert res.status_code == 201
    assert res.data["number"] == next_number
    assert len(res.data["lines"]) == len(bill_data["lines"])
    next_number = get_bill_next_number()
    res = client.post(url, bill_data, format="json")
    assert res.data["number"] == next_number

    # test transaction, bill is draft so transaction should not exist
    bill_id = res.data["id"]
    contenttype = ContentType.objects.get(app_label="bill", model="bill")
    assert (
        Transaction.objects.filter(ref_type=contenttype, ref_id=bill_id).exists()
        is False
    )
    # mark bill as open, transaction should exist now
    url = reverse("bill-mark-as-open", kwargs={"pk": bill_id})
    res = client.post(url)
    assert Transaction.objects.filter(ref_type=contenttype, ref_id=bill_id).exists()

    # list
    url = reverse("bill-list")
    res = client.get(url)
    assert res.status_code == 200

    # total outstanding
    url = reverse("bill-outstanding")
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_retrieve_update_delete_bill(
    client, test_user, bill_object, bill_data, bill_data_partial
):
    url = reverse("bill-detail", kwargs={"pk": bill_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, bill_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, bill_data_partial, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_bill", "change_bill", "delete_bill")

    res = client.get(url)
    assert res.status_code == 200
    assert res.data["id"] == bill_object.id

    res = client.patch(url, bill_data_partial, format="json")
    assert res.status_code == 200
    assert len(res.data["lines"]) == len(bill_data_partial["lines"])

    res = client.put(url, bill_data, format="json")
    assert res.status_code == 200
    assert len(res.data["lines"]) == len(bill_data["lines"])

    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_bill_update_should_fail(
    client, test_user, bill_object, bill_data_with_invalid_lines
):
    url = reverse("bill-list")
    test_user.add_permissions("add_bill", "change_bill")
    res = client.post(url, bill_data_with_invalid_lines, format="json")
    assert res.status_code == 400

    url = reverse("bill-detail", kwargs={"pk": bill_object.pk})
    res = client.put(url, bill_data_with_invalid_lines, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_create_list_payment(client, test_user, payment_made_data, bill_object):
    url = reverse("payment-made-list")
    # no permissions
    res = client.post(url, payment_made_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_paymentmade", "view_paymentmade")
    res = client.post(url, payment_made_data, format="json")
    assert res.status_code == 201

    res = client.get(url)
    assert res.status_code == 200

    # test bill filtering
    url = url + "?bill=" + str(bill_object.id)
    res = client.get(url)
    assert res.status_code == 200
    assert res.data[0]["bill"]["id"] == bill_object.id


@pytest.mark.django_db
def test_retrieve_update_delete_payment(
    client, test_user, payment_made_data, payment_made_object
):
    url = reverse("payment-made-detail", kwargs={"pk": payment_made_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, payment_made_data)
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions(
        "view_paymentmade", "change_paymentmade", "delete_paymentmade"
    )
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["bill"]["vendor"] == payment_made_object.bill.vendor.display_name

    res = client.put(url, payment_made_data, format="json")
    assert res.status_code == 200
    assert float(res.data["amount"]) == payment_made_data["amount"]

    res = client.patch(url, payment_made_data, format="json")
    assert res.status_code == 200

    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_bill_status_update(client, test_user):
    bill_line = mixer.blend("bill.BillLine", rate=10_000, quantity=2)
    bill = bill_line.bill
    payment_made_data = {
        "bill": bill.id,
        "amount": 5_000,
        "date": "2023-05-19",
        "mode": "Bank Transfer",
    }
    test_user.add_permissions(
        "view_bill",
        "add_bill",
        "add_paymentmade",
        "change_paymentmade",
        "delete_paymentmade",
        "view_transation",
    )
    contenttype = ContentType.objects.get(app_label="bill", model="bill")

    # mark bill as open
    url = reverse("bill-mark-as-open", kwargs={"pk": bill.pk})
    res = client.post(url)
    assert res.status_code == 204
    bill.refresh_from_db()
    assert bill.status == BillStatus.OPEN
    # test transaction
    assert Transaction.objects.filter(ref_type=contenttype, ref_id=bill.id).exists()

    # move bill to draft
    url = reverse("bill-move-to-draft", kwargs={"pk": bill.pk})
    res = client.post(url)
    assert res.status_code == 204
    bill.refresh_from_db()
    assert bill.status == BillStatus.DRAFT
    # test transaction
    assert (
        Transaction.objects.filter(ref_type=contenttype, ref_id=bill.id).exists()
        is False
    )

    # add payment (partial)
    url = reverse("payment-made-list")
    res = client.post(url, payment_made_data, format="json")
    assert res.status_code == 201
    bill.refresh_from_db()
    assert bill.is_draft is False
    assert bill.status == BillStatus.PARTLY_PAID

    # change payment amount
    url = reverse("payment-made-detail", kwargs={"pk": int(res.data["id"])})
    payment_made_data["amount"] = 15_000
    res = client.put(url, payment_made_data, format="json")
    assert res.status_code == 200
    bill.refresh_from_db()
    assert bill.status == BillStatus.PARTLY_PAID

    # add payment (full)
    url = reverse("payment-made-list")
    payment_made_data["amount"] = 5_000
    res = client.post(url, payment_made_data, format="json")
    assert res.status_code == 201
    bill.refresh_from_db()
    assert bill.status == BillStatus.PAID

    # delete payment
    url = reverse("payment-made-detail", kwargs={"pk": int(res.data["id"])})
    res = client.delete(url)
    assert res.status_code == 204
    bill.refresh_from_db()
    assert bill.status == BillStatus.PARTLY_PAID
