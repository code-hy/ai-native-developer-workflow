import pytest
from django.core.cache import cache
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_login_rate_limit_blocks_sixth_attempt(client):
    cache.clear()
    User.objects.create_user(
        username="rater", email="rate@example.com", password="CorrectPass123!"
    )
    url = reverse("accounts:login")
    # 5 failed attempts
    for _i in range(5):
        resp = client.post(
            url, {"username": "rate@example.com", "password": "WrongPass"}
        )
        # should be 200 with form error, not 429 yet
        assert resp.status_code == 200
        assert b"correct" in resp.content.lower() or b"error" in resp.content.lower()

    # 6th attempt should be 429
    resp = client.post(url, {"username": "rate@example.com", "password": "WrongPass"})
    assert resp.status_code == 429
    assert (
        b"Too Many Requests" in resp.content or b"rate limited" in resp.content.lower()
    )

    # even correct password should still be blocked while rate limited
    resp = client.post(
        url, {"username": "rate@example.com", "password": "CorrectPass123!"}
    )
    assert resp.status_code == 429


def test_login_success_resets_rate_limit(client):
    cache.clear()
    User.objects.create_user(
        username="rater2", email="rate2@example.com", password="CorrectPass123!"
    )
    url = reverse("accounts:login")
    # 3 failed
    for _ in range(3):
        client.post(url, {"username": "rate2@example.com", "password": "Wrong"})
    # successful login
    resp = client.post(
        url, {"username": "rate2@example.com", "password": "CorrectPass123!"}
    )
    assert resp.status_code == 302
    # next failure should not be rate limited immediately (counter reset)
    resp = client.post(url, {"username": "rate2@example.com", "password": "Wrong"})
    assert resp.status_code == 200
