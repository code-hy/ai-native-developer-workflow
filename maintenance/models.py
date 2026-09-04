from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class MaintenanceTask(models.Model):
    household = models.ForeignKey(
        "households.Household",
        on_delete=models.CASCADE,
        related_name="maintenance_tasks",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    interval_days = models.PositiveIntegerField(help_text="Repeat every N days")
    last_done_at = models.DateTimeField(null=True, blank=True)
    next_due_at = models.DateTimeField()
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.title} due {self.next_due_at}"

    def mark_done(self):
        self.last_done_at = timezone.now()
        self.next_due_at = self.last_done_at + timedelta(days=self.interval_days)
        self.save(update_fields=["last_done_at", "next_due_at"])

    def is_overdue(self) -> bool:
        return self.next_due_at < timezone.now()
