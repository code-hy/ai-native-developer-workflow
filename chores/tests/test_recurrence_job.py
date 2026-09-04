from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_recurring_creates_next_instance():
    user = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=user
    )
    Membership.objects.create(
        user=user, household=household, role=Membership.Role.ADMIN
    )
    due = timezone.now() - timedelta(days=1)
    Chore.objects.create(
        household=household,
        title="Weekly Trash",
        category="trash",
        effort=2,
        due_at=due,
        rrule="FREQ=WEEKLY;BYDAY=MO",
        status=Chore.Status.COMPLETED,
        completed_at=timezone.now(),
        created_by=user,
    )
    out = StringIO()
    call_command("generate_due_instances", stdout=out)
    # should have created one next
    assert Chore.objects.filter(title="Weekly Trash", status=Chore.Status.TODO).exists()
    nxt = Chore.objects.get(title="Weekly Trash", status=Chore.Status.TODO)
    assert nxt.due_at > due
    # second run should not duplicate
    call_command("generate_due_instances", stdout=StringIO())
    assert (
        Chore.objects.filter(title="Weekly Trash", status=Chore.Status.TODO).count()
        == 1
    )
