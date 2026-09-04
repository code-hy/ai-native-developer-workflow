from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_dashboard_counts(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    Chore.objects.create(
        household=h,
        title="Overdue",
        category="trash",
        effort=1,
        due_at=timezone.now() - timedelta(days=1),
        created_by=u,
    )
    Chore.objects.create(
        household=h,
        title="Today",
        category="trash",
        effort=1,
        due_at=timezone.now(),
        created_by=u,
    )
    Chore.objects.create(
        household=h,
        title="Mine",
        category="trash",
        effort=1,
        due_at=timezone.now() + timedelta(days=1),
        assignee=u,
        created_by=u,
    )
    client.force_login(u)
    resp = client.get(reverse("dashboard"))
    assert resp.status_code == 200
    assert b"Overdue" in resp.content


def test_chore_ical_and_household_filters(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    Chore.objects.create(
        household=h,
        title="Ical",
        category="other",
        effort=1,
        due_at=timezone.now() + timedelta(days=1),
        created_by=u,
    )
    client.force_login(u)
    resp = client.get(reverse("chores:ical"))
    assert resp.status_code == 200
    assert b"BEGIN:VCALENDAR" in resp.content
    assert b"Ical" in resp.content
