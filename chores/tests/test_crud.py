from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from chores.models import Chore
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_create_chore_appears_in_list(client):
    user = User.objects.create_user(
        username="u", email="u@example.com", password="pass12345!"
    )
    household = Household.objects.create(
        name="H", type="roommates", timezone="UTC", created_by=user
    )
    Membership.objects.create(
        user=user, household=household, role=Membership.Role.ADMIN
    )
    client.force_login(user)
    due = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
    resp = client.post(
        reverse("chores:create", kwargs={"household_id": household.pk}),
        {
            "title": "Dishes",
            "description": "Wash dishes",
            "category": "kitchen",
            "effort": 3,
            "minutes": 10,
            "due_at": due,
        },
    )
    assert resp.status_code == 302
    assert Chore.objects.filter(title="Dishes", household=household).exists()
    resp = client.get(reverse("chores:list") + f"?household={household.pk}")
    assert resp.status_code == 200
    assert b"Dishes" in resp.content
