import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Household(models.Model):
    class Type(models.TextChoices):
        ROOMMATES = "roommates", "Roommates"
        FAMILY = "family", "Family"
        COUPLE = "couple", "Couple"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.ROOMMATES)
    timezone = models.CharField(max_length=50, default="UTC")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_households",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_type_display()})"


class Membership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"
        PARENT = "parent", "Parent"
        CHILD = "child", "Child"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "household")]

    def __str__(self) -> str:
        return f"{self.user} -> {self.household} ({self.role})"


class Invite(models.Model):
    household = models.ForeignKey(
        Household, on_delete=models.CASCADE, related_name="invites"
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, db_index=True)
    role = models.CharField(
        max_length=20, choices=Membership.Role.choices, default=Membership.Role.MEMBER
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_invites",
    )

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        # normalize email
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_expired() and self.accepted_at is None

    def __str__(self) -> str:
        return f"Invite {self.email} -> {self.household} token={self.token[:8]}..."
