import pytest
from django.urls import reverse

from accounts.models import User
from groceries.models import GroceryItem
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_grocery_add_and_toggle(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    client.force_login(u)
    resp = client.post(
        reverse("groceries:add"), {"household": h.pk, "name": "Milk", "qty": "1L"}
    )
    assert resp.status_code == 302
    item = GroceryItem.objects.get(name="Milk")
    assert item.checked is False
    resp = client.post(reverse("groceries:toggle", kwargs={"pk": item.pk}))
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.checked is True
    assert item.checked_by == u


def test_grocery_list_scoped(client):
    u1 = User.objects.create_user(
        username="u1", email="u1@example.com", password="pass12345!"
    )
    u2 = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    h1 = Household.objects.create(
        name="H1", type="roommates", timezone="UTC", created_by=u1
    )
    h2 = Household.objects.create(
        name="H2", type="roommates", timezone="UTC", created_by=u2
    )
    Membership.objects.create(user=u1, household=h1, role=Membership.Role.ADMIN)
    Membership.objects.create(user=u2, household=h2, role=Membership.Role.ADMIN)
    GroceryItem.objects.create(household=h1, name="Apple123", added_by=u1)
    GroceryItem.objects.create(household=h2, name="Banana456", added_by=u2)
    client.force_login(u1)
    resp = client.get(reverse("groceries:list"), {"household": h1.pk})
    assert resp.status_code == 200
    assert b"Apple123" in resp.content
    assert b"Banana456" not in resp.content
