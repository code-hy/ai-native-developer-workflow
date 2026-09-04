from django.contrib import admin

from .models import Chore


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ["title", "household", "assignee", "status", "effort", "due_at"]
    list_filter = ["status", "category"]
