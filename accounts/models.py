from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if not self.username:
            # generate username from email prefix, ensure uniqueness
            base = (self.email.split("@")[0] if self.email else "user")[:30]
            candidate = base
            suffix = 1
            while User.objects.filter(username=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}{suffix}"[:150]
                suffix += 1
            self.username = candidate
        if self.email:
            self.email = self.email.lower().strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email
