from django.conf import settings
from django.db import models


class Bill(models.Model):
    class Status(models.TextChoices):
        DUE = "due", "Due"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    household = models.ForeignKey(
        "households.Household", on_delete=models.CASCADE, related_name="bills"
    )
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    due_at = models.DateTimeField()
    rrule = models.CharField(max_length=200, blank=True)
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bills_to_pay",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DUE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} {self.amount} due {self.due_at}"

    def is_overdue(self) -> bool:
        from django.utils import timezone

        return self.status != self.Status.PAID and self.due_at < timezone.now()
