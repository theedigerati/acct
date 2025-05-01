import pytest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from apps.accounting.models import Transaction
from apps.sales.invoice.models import InvoiceStatus, get_invoice_next_number
from mixer.backend.django import mixer


@pytest.mark.django_db
def test_create_list_invoice(
    client,
    test_user,
    invoice_data,
):
    url = reverse("invoice-list")
    # no permissions
    res = client.post(url, invoice_data)
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_invoice", "view_invoice", "view_transation")
    # create
    next_number = get_invoice_next_number()
    res = client.post(url, invoice_data, format="json")
    assert res.status_code == 201
    assert res.data["number"] == next_number
    assert len(res.data["lines"]) == len(invoice_data["lines"])
    next_number = get_invoice_next_number()
    res = client.post(url, invoice_data, format="json")
    assert res.data["number"] == next_number

    # test transaction, invoice is draft so transaction should not exist
    invoice_id = res.data["id"]
    contenttype = ContentType.objects.get(app_label="invoice", model="invoice")
    assert (
        Transaction.objects.filter(ref_type=contenttype, ref_id=invoice_id).exists()
        is False
    )
    # mark invoice as sent, transaction should exist now
    url = reverse("invoice-mark-as-sent", kwargs={"pk": invoice_id})
    res = client.post(url)
    assert Transaction.objects.filter(ref_type=contenttype, ref_id=invoice_id).exists()

    # list
    url = reverse("invoice-list")
    res = client.get(url)
    assert res.status_code == 200

    # total outstanding
    url = reverse("invoice-outstanding")
    res = client.get(url)
    assert res.status_code == 200


@pytest.mark.django_db
def test_retrieve_update_delete_invoice(
    client, test_user, invoice_object, invoice_data, invoice_data_partial
):
    url = reverse("invoice-detail", kwargs={"pk": invoice_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, invoice_data, format="json")
    assert res.status_code == 403
    res = client.patch(url, invoice_data_partial, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_invoice", "change_invoice", "delete_invoice")

    res = client.get(url)
    assert res.status_code == 200
    assert res.data["id"] == invoice_object.id

    res = client.patch(url, invoice_data_partial, format="json")
    assert res.status_code == 200
    assert len(res.data["lines"]) == len(invoice_data_partial["lines"])

    res = client.put(url, invoice_data, format="json")
    assert res.status_code == 200
    assert len(res.data["lines"]) == len(invoice_data["lines"])

    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_invoice_update_should_fail(
    client, test_user, invoice_object, invoice_data_with_invalid_lines
):
    url = reverse("invoice-list")
    test_user.add_permissions("add_invoice", "change_invoice")
    res = client.post(url, invoice_data_with_invalid_lines, format="json")
    assert res.status_code == 400

    url = reverse("invoice-detail", kwargs={"pk": invoice_object.pk})
    res = client.put(url, invoice_data_with_invalid_lines, format="json")
    assert res.status_code == 400


@pytest.mark.django_db
def test_create_list_payment(client, test_user, payment_received_data, invoice_object):
    url = reverse("payment-received-list")
    # no permissions
    res = client.post(url, payment_received_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_paymentreceived", "view_paymentreceived")
    # create
    res = client.post(url, payment_received_data, format="json")
    assert res.status_code == 201
    # list
    res = client.get(url)
    assert res.status_code == 200

    # test invoice filtering
    url = url + "?invoice=" + str(invoice_object.id)
    res = client.get(url)
    assert res.status_code == 200
    assert res.data[0]["invoice"]["id"] == invoice_object.id


@pytest.mark.django_db
def test_retrieve_update_delete_payment(
    client, test_user, payment_received_data, payment_received_object
):
    url = reverse("payment-received-detail", kwargs={"pk": payment_received_object.pk})

    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, payment_received_data)
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions(
        "view_paymentreceived", "change_paymentreceived", "delete_paymentreceived"
    )
    res = client.get(url)
    assert res.status_code == 200
    assert (
        res.data["invoice"]["client"]
        == payment_received_object.invoice.client.display_name
    )

    res = client.put(url, payment_received_data, format="json")
    assert res.status_code == 200
    assert float(res.data["amount"]) == payment_received_data["amount"]

    res = client.patch(url, payment_received_data, format="json")
    assert res.status_code == 200

    res = client.delete(url)
    assert res.status_code == 204


@pytest.mark.django_db
def test_invoice_status_update(client, test_user):
    invoice_line = mixer.blend("invoice.InvoiceLine", rate=10_000, quantity=2)
    invoice = invoice_line.invoice
    payment_received_data = {
        "invoice": invoice.id,
        "amount": 5_000,
        "date": "2023-05-19",
        "mode": "Bank Transfer",
    }
    test_user.add_permissions(
        "view_invoice",
        "add_invoice",
        "add_paymentreceived",
        "change_paymentreceived",
        "delete_paymentreceived",
        "view_transaction",
    )
    contenttype = ContentType.objects.get(app_label="invoice", model="invoice")

    # mark invoice as sent
    url = reverse("invoice-mark-as-sent", kwargs={"pk": invoice.pk})
    res = client.post(url)
    assert res.status_code == 204
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.SENT
    # test transaction
    assert Transaction.objects.filter(ref_type=contenttype, ref_id=invoice.id).exists()

    # move invoice to draft
    url = reverse("invoice-move-to-draft", kwargs={"pk": invoice.pk})
    res = client.post(url)
    assert res.status_code == 204
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.DRAFT
    # test transaction
    assert (
        Transaction.objects.filter(ref_type=contenttype, ref_id=invoice.id).exists()
        is False
    )

    # add payment (partial)
    url = reverse("payment-received-list")
    res = client.post(url, payment_received_data, format="json")
    assert res.status_code == 201
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PARTLY_PAID

    # change payment amount
    url = reverse("payment-received-detail", kwargs={"pk": int(res.data["id"])})
    payment_received_data["amount"] = 15_000
    res = client.put(url, payment_received_data, format="json")
    assert res.status_code == 200
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PARTLY_PAID

    # add payment (full)
    url = reverse("payment-received-list")
    payment_received_data["amount"] = 5_000
    res = client.post(url, payment_received_data, format="json")
    assert res.status_code == 201
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PAID

    # delete payment
    url = reverse("payment-received-detail", kwargs={"pk": int(res.data["id"])})
    res = client.delete(url)
    assert res.status_code == 204
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PARTLY_PAID
