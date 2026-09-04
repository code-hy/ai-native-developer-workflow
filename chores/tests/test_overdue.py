from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_overdue_computed_server_side():
    user = User.objects.create_user(
        username="u2", email="u2@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="H2", type="roommates", timezone="UTC", created_by=user
    )
    Membership.objects.create(
        user=user, household=household, role=Membership.Role.ADMIN
    )
    # overdue due_at in past
    chore = Chore.objects.create(
        household=household,
        title="Old",
        category="trash",
        effort=2,
        due_at=timezone.now() - timedelta(days=1),
        created_by=user,
    )
    assert chore.is_overdue() is True
    # not overdue if completed even if due past
    chore2 = Chore.objects.create(
        household=household,
        title="Done",
        category="trash",
        effort=2,
        due_at=timezone.now() - timedelta(days=1),
        status=Chore.Status.COMPLETED,
        created_by=user,
    )
    assert chore2.is_overdue() is False
    # not overdue if due future
    chore3 = Chore.objects.create(
        household=household,
        title="Future",
        category="trash",
        effort=2,
        due_at=timezone.now() + timedelta(days=1),
        created_by=user,
    )
    assert chore3.is_overdue() is False
