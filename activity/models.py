from django.conf import settings
from django.db import models


class Activity(models.Model):
    household = models.ForeignKey(
        "households.Household", on_delete=models.CASCADE, related_name="activities"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=50)  # e.g., created, completed, claimed
    entity_type = models.CharField(max_length=50)  # chore, bill, grocery
    entity_id = models.PositiveIntegerField()
    diff = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["household", "created_at"])]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}#{self.entity_id} by {self.actor}"
