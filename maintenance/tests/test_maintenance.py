from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from households.models import Household, Membership
from maintenance.models import MaintenanceTask

pytestmark = pytest.mark.django_db


def test_maintenance_mark_done(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    task = MaintenanceTask.objects.create(
        household=h,
        title="Filter",
        interval_days=30,
        next_due_at=timezone.now() + timedelta(days=1),
    )
    client.force_login(u)
    resp = client.post(reverse("maintenance:done", kwargs={"pk": task.pk}))
    assert resp.status_code == 302
    task.refresh_from_db()
    assert task.last_done_at is not None
    assert task.next_due_at > timezone.now()


def test_maintenance_overdue():
    from datetime import timedelta

    from django.utils import timezone

    u = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    from households.models import Household

    h = Household.objects.create(
        name="H2", type="roommates", timezone="UTC", created_by=u
    )
    t = MaintenanceTask(
        household=h,
        title="Gutters",
        interval_days=180,
        next_due_at=timezone.now() - timedelta(days=1),
    )
    assert t.is_overdue() is True
