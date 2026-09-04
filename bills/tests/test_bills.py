from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bills.models import Bill
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_bill_toggle_and_recurring(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    bill = Bill.objects.create(
        household=h,
        name="Rent",
        amount=100,
        due_at=timezone.now() + timedelta(days=1),
        rrule="FREQ=MONTHLY",
        payer=u,
    )
    client.force_login(u)
    resp = client.post(reverse("bills:toggle", kwargs={"pk": bill.pk}))
    assert resp.status_code == 302
    bill.refresh_from_db()
    assert bill.status == Bill.Status.PAID
    assert Bill.objects.filter(name="Rent", status=Bill.Status.DUE).exists()


def test_bill_overdue():
    from datetime import timedelta

    from django.utils import timezone

    from accounts.models import User
    from bills.models import Bill
    from households.models import Household

    u = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H2", type="roommates", timezone="UTC", created_by=u
    )
    b = Bill(
        household=h, name="X", amount=10, due_at=timezone.now() - timedelta(days=1)
    )
    assert b.is_overdue() is True
    b.status = Bill.Status.PAID
    assert b.is_overdue() is False
