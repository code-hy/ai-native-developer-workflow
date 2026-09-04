from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_activity_created_on_chore(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    client.force_login(u)
    due = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    client.post(
        reverse("chores:create", kwargs={"household_id": h.pk}),
        {"title": "Act", "category": "other", "effort": 2, "due_at": due},
    )
    from activity.models import Activity

    assert Activity.objects.filter(household=h, entity_type="chore").exists()


def test_activity_export_csv(client):
    u = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u
    )
    Membership.objects.create(user=u, household=h, role=Membership.Role.ADMIN)
    client.force_login(u)
    resp = client.get(reverse("activity:export"))
    assert resp.status_code == 200
    assert b"household" in resp.content


def test_fairness_scores():
    from chores.services.fairness import fairness_scores

    u1 = User.objects.create_user(
        username="u1", email="u1@example.com", password="pass12345!"
    )
    u2 = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    h = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u1
    )
    Membership.objects.create(user=u1, household=h, role=Membership.Role.ADMIN)
    Membership.objects.create(user=u2, household=h, role=Membership.Role.ADMIN)
    Chore.objects.create(
        household=h,
        title="A",
        category="other",
        effort=5,
        due_at=timezone.now(),
        status=Chore.Status.COMPLETED,
        completed_at=timezone.now(),
        assignee=u1,
        created_by=u1,
    )
    Chore.objects.create(
        household=h,
        title="B",
        category="other",
        effort=3,
        due_at=timezone.now(),
        status=Chore.Status.COMPLETED,
        completed_at=timezone.now(),
        assignee=u2,
        created_by=u2,
    )
    scores = fairness_scores(h, window="month")
    assert scores[u1.pk] == 5
    assert scores[u2.pk] == 3
