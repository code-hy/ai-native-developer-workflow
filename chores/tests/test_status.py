from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_complete_chore(client):
    user = User.objects.create_user(
        username="u3", email="u3@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="H3", type="roommates", timezone="UTC", created_by=user
    )
    Membership.objects.create(
        user=user, household=household, role=Membership.Role.ADMIN
    )
    chore = Chore.objects.create(
        household=household,
        title="Mop",
        category="living",
        effort=2,
        due_at=timezone.now() + timedelta(days=1),
        created_by=user,
    )
    client.force_login(user)
    resp = client.post(reverse("chores:complete", kwargs={"chore_id": chore.pk}))
    assert resp.status_code == 302
    chore.refresh_from_db()
    assert chore.status == Chore.Status.COMPLETED
    assert chore.completed_at is not None
    # second complete should not error 500 but redirect with error message (still 302 per view)
    resp2 = client.post(reverse("chores:complete", kwargs={"chore_id": chore.pk}))
    assert resp2.status_code == 302
    chore.refresh_from_db()
    assert chore.status == Chore.Status.COMPLETED
