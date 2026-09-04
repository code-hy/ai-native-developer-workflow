from django.conf import settings
from django.db import models


class GroceryItem(models.Model):
    household = models.ForeignKey(
        "households.Household", on_delete=models.CASCADE, related_name="grocery_items"
    )
    name = models.CharField(max_length=200)
    qty = models.CharField(max_length=50, default="1", blank=True)
    checked = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="added_groceries",
    )
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_groceries",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["checked", "-updated_at"]

    def __str__(self) -> str:
        return f"{self.name} x{self.qty} ({'checked' if self.checked else 'todo'})"
