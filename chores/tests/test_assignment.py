from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_pool_claim(client):
    u1 = User.objects.create_user(
        username="u1", email="u1@example.com", password="pass12345!"
    )
    u2 = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=u1
    )
    Membership.objects.create(user=u1, household=household, role=Membership.Role.ADMIN)
    Membership.objects.create(user=u2, household=household, role=Membership.Role.MEMBER)
    chore = Chore.objects.create(
        household=household,
        title="Pool Chore",
        category="other",
        effort=1,
        due_at=timezone.now() + timedelta(days=1),
        created_by=u1,
    )
    assert chore.assignee is None
    client.force_login(u2)
    resp = client.post(reverse("chores:claim", kwargs={"chore_id": chore.pk}))
    assert resp.status_code == 302
    chore.refresh_from_db()
    assert chore.assignee == u2


def test_rotating_round_robin(client):
    # Create 3 members A,B,C with ordered joined_at
    users = []
    for i, email in enumerate(["a@example.com", "b@example.com", "c@example.com"]):
        u = User.objects.create_user(
            username=f"u{i}", email=email, password="pass12345!"
        )
        users.append(u)
    household = Household.objects.create(
        name="Flat", type="roommates", timezone="UTC", created_by=users[0]
    )
    for u in users:
        Membership.objects.create(
            user=u, household=household, role=Membership.Role.MEMBER
        )
    # create recurring chore assigned to A, due 6 days ago so next is within horizon
    due = timezone.now() - timedelta(days=1)
    Chore.objects.create(
        household=household,
        title="Rotating",
        category="kitchen",
        effort=2,
        due_at=due,
        rrule="FREQ=DAILY",
        assignee=users[0],
        status=Chore.Status.COMPLETED,
        completed_at=timezone.now(),
        created_by=users[0],
    )
    # generate next should be B
    call_command("generate_due_instances", stdout=StringIO())
    nxt = Chore.objects.filter(title="Rotating", status=Chore.Status.TODO).first()
    assert nxt is not None
    assert nxt.assignee == users[1]
    # complete B's chore and generate next -> C
    nxt.status = Chore.Status.COMPLETED
    nxt.completed_at = timezone.now()
    nxt.save()
    call_command("generate_due_instances", stdout=StringIO())
    nxt2 = Chore.objects.filter(title="Rotating", status=Chore.Status.TODO).first()
    assert nxt2.assignee == users[2]
    # complete C -> back to A
    nxt2.status = Chore.Status.COMPLETED
    nxt2.completed_at = timezone.now()
    nxt2.save()
    call_command("generate_due_instances", stdout=StringIO())
    nxt3 = Chore.objects.filter(title="Rotating", status=Chore.Status.TODO).first()
    assert nxt3.assignee == users[0]


def test_child_cannot_delete(client):
    parent = User.objects.create_user(
        username="parent", email="parent@example.com", password="pass12345!"
    )
    child = User.objects.create_user(
        username="child", email="child@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="Fam", type="family", timezone="UTC", created_by=parent
    )
    Membership.objects.create(
        user=parent, household=household, role=Membership.Role.PARENT
    )
    Membership.objects.create(
        user=child, household=household, role=Membership.Role.CHILD
    )
    chore = Chore.objects.create(
        household=household,
        title="X",
        category="other",
        effort=1,
        due_at=timezone.now() + timedelta(days=1),
        created_by=parent,
    )
    client.force_login(child)
    resp = client.post(reverse("chores:delete", kwargs={"chore_id": chore.pk}))
    assert resp.status_code == 403
    assert Chore.objects.filter(pk=chore.pk).exists()
