import pytest
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_signup_creates_user_and_redirects(client):
    url = reverse("accounts:signup")
    data = {
        "email": "newuser@example.com",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    }
    resp = client.post(url, data)
    assert resp.status_code == 302
    assert resp.url == reverse("households:create")
    user = User.objects.get(email="newuser@example.com")
    assert user.check_password("StrongPass123!")
    # password is hashed, not plain
    assert user.password != "StrongPass123!"
    assert user.password.startswith("pbkdf2_") or user.password.startswith("argon2")


def test_signup_duplicate_email_fails(client):
    User.objects.create_user(
        username="test", email="dup@example.com", password="StrongPass123!"
    )
    url = reverse("accounts:signup")
    data = {
        "email": "dup@example.com",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    }
    resp = client.post(url, data)
    assert resp.status_code == 200  # form invalid, re-render
    assert b"already exists" in resp.content


def test_login_success(client):
    User.objects.create_user(
        username="tester", email="login@example.com", password="StrongPass123!"
    )
    resp = client.post(
        reverse("accounts:login"),
        {"username": "login@example.com", "password": "StrongPass123!"},
    )
    # successful login redirects to dashboard or next
    assert resp.status_code == 302
    assert (
        resp.wsgi_request.user.is_authenticated
        or client.session.get("_auth_user_id") is not None
    )
