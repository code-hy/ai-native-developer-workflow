from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from households.models import Household, Invite, Membership

pytestmark = pytest.mark.django_db


def test_invite_flow_creates_membership(client):
    admin = User.objects.create_user(
        username="admin", email="admin@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="Test House", type="roommates", timezone="UTC", created_by=admin
    )
    Membership.objects.create(
        user=admin, household=household, role=Membership.Role.ADMIN
    )

    # admin invites guest
    client.force_login(admin)
    resp = client.post(
        reverse("households:invite", kwargs={"pk": household.pk}),
        {"email": "guest@example.com", "role": "member"},
    )
    assert resp.status_code == 302
    invite = Invite.objects.get(email="guest@example.com")
    assert invite.household == household
    assert invite.is_valid()
    token = invite.token

    # guest signs up and accepts
    client.logout()
    guest = User.objects.create_user(
        username="guest", email="guest@example.com", password="GuestPass123!"
    )
    client.force_login(guest)
    resp = client.get(f"/invite/{token}/")
    assert resp.status_code == 302
    assert resp.url == reverse("households:detail", kwargs={"pk": household.pk})
    # membership created
    assert Membership.objects.filter(user=guest, household=household).exists()
    invite.refresh_from_db()
    assert invite.accepted_at is not None
    assert invite.accepted_by == guest
    # second use should be 410
    resp = client.get(f"/invite/{token}/")
    assert resp.status_code == 410


def test_invite_expired_returns_410(client):
    admin = User.objects.create_user(
        username="admin2", email="admin2@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="House2", type="family", timezone="UTC", created_by=admin
    )
    Membership.objects.create(
        user=admin, household=household, role=Membership.Role.ADMIN
    )
    invite = Invite.objects.create(
        household=household,
        email="late@example.com",
        created_by=admin,
        expires_at=timezone.now() - timedelta(days=1),
    )
    token = invite.token
    guest = User.objects.create_user(
        username="late", email="late@example.com", password="Pass12345!"
    )
    client.force_login(guest)
    resp = client.get(f"/invite/{token}/")
    assert resp.status_code == 410


def test_invite_requires_login_redirects(client):
    admin = User.objects.create_user(
        username="admin3", email="admin3@example.com", password="Pass12345!"
    )
    household = Household.objects.create(
        name="House3", type="couple", timezone="UTC", created_by=admin
    )
    Membership.objects.create(
        user=admin, household=household, role=Membership.Role.ADMIN
    )
    invite = Invite.objects.create(
        household=household, email="new@example.com", created_by=admin
    )
    token = invite.token
    # anonymous GET should redirect to signup with next
    resp = client.get(f"/invite/{token}/")
    assert resp.status_code == 302
    assert "/accounts/signup/" in resp.url
    # after signup, session should redirect to invite
    # test signup with pending token
    resp = client.post(
        reverse("accounts:signup"),
        {
            "email": "new@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )
    # signup should redirect to invite accept
    assert resp.status_code == 302
    assert f"/invite/{token}/" in resp.url
