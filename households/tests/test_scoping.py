import pytest
from django.urls import reverse

from accounts.models import User
from households.models import Household, Membership

pytestmark = pytest.mark.django_db


def test_household_detail_scoping_forbidden_for_outsider(client):
    owner = User.objects.create_user(
        username="owner", email="owner@example.com", password="Pass12345!"
    )
    outsider = User.objects.create_user(
        username="outsider", email="outsider@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="Private House", type="roommates", timezone="UTC", created_by=owner
    )
    Membership.objects.create(
        user=owner, household=household, role=Membership.Role.ADMIN
    )

    client.force_login(outsider)
    resp = client.get(reverse("households:detail", kwargs={"pk": household.pk}))
    assert resp.status_code == 403


def test_household_detail_allowed_for_member(client):
    owner = User.objects.create_user(
        username="owner2", email="owner2@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="My House", type="family", timezone="UTC", created_by=owner
    )
    Membership.objects.create(
        user=owner, household=household, role=Membership.Role.ADMIN
    )
    client.force_login(owner)
    resp = client.get(reverse("households:detail", kwargs={"pk": household.pk}))
    assert resp.status_code == 200
    assert b"My House" in resp.content


def test_household_list_only_shows_own(client):
    u1 = User.objects.create_user(
        username="u1", email="u1@example.com", password="Pass12345!"
    )
    u2 = User.objects.create_user(
        username="u2", email="u2@example.com", password="Pass12345!"
    )
    h1 = Household.objects.create(
        name="H1", type="roommates", timezone="UTC", created_by=u1
    )
    h2 = Household.objects.create(
        name="H2", type="roommates", timezone="UTC", created_by=u2
    )
    Membership.objects.create(user=u1, household=h1, role=Membership.Role.ADMIN)
    Membership.objects.create(user=u2, household=h2, role=Membership.Role.ADMIN)
    client.force_login(u1)
    resp = client.get(reverse("households:list"))
    assert resp.status_code == 200
    assert b"H1" in resp.content
    assert b"H2" not in resp.content


def test_child_cannot_invite(client):
    parent = User.objects.create_user(
        username="parent", email="parent@example.com", password="Pass12345!"
    )
    child = User.objects.create_user(
        username="child", email="child@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="Family", type="family", timezone="UTC", created_by=parent
    )
    Membership.objects.create(
        user=parent, household=household, role=Membership.Role.PARENT
    )
    Membership.objects.create(
        user=child, household=household, role=Membership.Role.CHILD
    )
    client.force_login(child)
    resp = client.post(
        reverse("households:invite", kwargs={"pk": household.pk}),
        {"email": "x@example.com", "role": "member"},
    )
    assert resp.status_code == 403
