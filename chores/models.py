from django.conf import settings
from django.db import models
from django.utils import timezone


class Chore(models.Model):
    class Category(models.TextChoices):
        KITCHEN = "kitchen", "Kitchen"
        BATHROOM = "bathroom", "Bathroom"
        LIVING = "living", "Living"
        TRASH = "trash", "Trash"
        LAUNDRY = "laundry", "Laundry"
        OUTDOOR = "outdoor", "Outdoor"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    household = models.ForeignKey(
        "households.Household", on_delete=models.CASCADE, related_name="chores"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.OTHER
    )
    effort = models.PositiveSmallIntegerField(default=3)  # 1-5
    minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Estimated minutes"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TODO
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_chores",
    )
    rrule = models.CharField(
        max_length=200, blank=True, help_text="RFC5545 rrule or empty"
    )
    due_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    proof = models.FileField(upload_to="proofs/%Y/%m/", null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_chores",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_at"]
        indexes = [
            models.Index(fields=["household", "status", "due_at"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"

    def is_overdue(self) -> bool:
        return self.status != self.Status.COMPLETED and self.due_at < timezone.now()

    def mark_completed(self) -> None:
        if self.status == self.Status.COMPLETED:
            raise ValueError("Already completed")
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
