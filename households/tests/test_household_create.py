import pytest
from django.urls import reverse

from accounts.models import User
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_household_create_sets_admin_membership(client):
    user = User.objects.create_user(
        username="creator", email="creator@example.com", password="Pass12345!"
    )
    client.force_login(user)
    resp = client.post(
        reverse("households:create"),
        {"name": "Sunset Flat", "type": "roommates", "timezone": "UTC"},
    )
    assert resp.status_code == 302
    h = Household.objects.get(name="Sunset Flat")
    assert h.created_by == user
    assert Membership.objects.filter(
        user=user, household=h, role=Membership.Role.ADMIN
    ).exists()


def test_household_create_requires_login(client):
    resp = client.get(reverse("households:create"))
    assert resp.status_code == 302  # redirect to login
    assert "/accounts/login/" in resp.url


def test_household_create_invalid_shows_error(client):
    user = User.objects.create_user(
        username="u", email="u@example.com", password="Pass12345!"
    )
    client.force_login(user)
    resp = client.post(
        reverse("households:create"),
        {"name": "", "type": "roommates", "timezone": "UTC"},
    )
    assert resp.status_code == 200
    assert b"This field is required" in resp.content
