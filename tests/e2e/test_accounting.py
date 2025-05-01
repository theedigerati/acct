import pytest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from apps.accounting.models import Transaction, get_journal_next_number


@pytest.mark.django_db()
def test_create_list_account(client, test_user, account_data):
    url = reverse("account-list")
    # no permissions
    res = client.post(url, account_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_account", "view_account")
    res_create = client.post(url, account_data, format="json")
    assert res_create.status_code == 201
    print(res_create.data["sub_type"]["id"])
    assert res_create.data["sub_type"]["id"] == account_data["sub_type"]
    res = client.get(url)
    assert res.status_code == 200

    # balances
    url = reverse("account-balance")
    res = client.get(url)
    assert res.status_code == 200
    assert res_create.data["id"] in res.data


@pytest.mark.django_db()
def test_retrieve_update_delete_account(
    client,
    test_user,
    account_data,
    editable_account_object,
    non_editable_account_object,
):
    url = reverse("account-detail", kwargs={"pk": editable_account_object.pk})
    # no permissions
    res = client.get(url)
    assert res.status_code == 403
    res = client.put(url, data=account_data, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("view_account", "change_account", "delete_account")
    # retrieve
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["code"] == editable_account_object.code

    # sibling accounts
    url = reverse("account-siblings", kwargs={"pk": editable_account_object.pk})
    res = client.get(url)
    assert res.status_code == 200
    assert res.data["sub_types"]
    assert res.data["accounts"]
    # transactions
    url = reverse("account-transactions", kwargs={"pk": editable_account_object.pk})
    res = client.get(url)
    assert res.status_code == 200

    # update
    url = reverse("account-detail", kwargs={"pk": editable_account_object.pk})
    res = client.put(url, account_data, format="json")
    assert res.status_code == 200
    # delete
    res = client.delete(url)
    assert res.status_code == 204
    # update fail
    url = reverse("account-detail", kwargs={"pk": non_editable_account_object.pk})
    res = client.put(url, account_data, format="json")
    assert res.status_code == 400
    # delete fail
    res = client.delete(url)
    assert res.status_code == 400


@pytest.mark.django_db
def test_crud_journal_entry(client, test_user, journal_data, invalid_journal_data):
    url = reverse("journal-entry-list")

    # no permisions
    res = client.post(url, journal_data, format="json")
    assert res.status_code == 403
    res = client.get(url)
    assert res.status_code == 403

    test_user.add_permissions("add_journalentry", "view_journalentry")

    # create
    next_number = get_journal_next_number()
    res = client.post(url, journal_data, format="json")
    assert res.status_code == 201
    assert res.data["number"] == next_number
    assert float(res.data["amount"]) == journal_data["lines"][0]["amount"]

    # test transaction, journal entry is draft so transaction should not exist
    journal_entry_id = res.data["id"]
    contenttype = ContentType.objects.get(app_label="accounting", model="journalentry")
    assert (
        Transaction.objects.filter(
            ref_type=contenttype, ref_id=journal_entry_id
        ).exists()
        is False
    )
    # mark journal_entry as published, transaction should exist now
    url = reverse("journal-entry-mark-as-published", kwargs={"pk": journal_entry_id})
    res = client.post(url)
    assert Transaction.objects.filter(
        ref_type=contenttype, ref_id=journal_entry_id
    ).exists()

    # create with invalid data
    url = reverse("journal-entry-list")
    journal_data["lines"].pop()
    res = client.post(url, journal_data, format="json")
    assert res.status_code == 400
    res = client.post(url, invalid_journal_data, format="json")
    assert res.status_code == 400

    # list
    res = client.get(url)
    assert res.status_code == 200

    # retrieve, update & delete
    url = reverse("journal-entry-detail", kwargs={"pk": res.data[0]["id"]})

    # retrieve
    res = client.get(url)
    assert res.status_code == 200

    # no permissions
    res = client.put(url, journal_data, format="json")
    assert res.status_code == 403
    res = client.delete(url)
    assert res.status_code == 403

    test_user.add_permissions("change_journalentry", "delete_journalentry")

    # update & delete
    res = client.put(url, journal_data, format="json")
    assert res.status_code == 405
    res = client.delete(url)
    assert res.status_code == 405
