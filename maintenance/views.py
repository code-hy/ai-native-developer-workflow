from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from households.models import Membership

from .models import MaintenanceTask


class MaintenanceListView(LoginRequiredMixin, ListView):
    model = MaintenanceTask
    template_name = "maintenance/list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        household_id = self.request.GET.get("household")
        if household_id:
            if not Membership.objects.filter(
                user=self.request.user, household_id=household_id
            ).exists():
                raise PermissionDenied
            return MaintenanceTask.objects.filter(household_id=household_id).order_by(
                "next_due_at"
            )
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )
        return MaintenanceTask.objects.filter(household_id__in=household_ids).order_by(
            "next_due_at"
        )


class MaintenanceDoneView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(MaintenanceTask, pk=pk)
        if not Membership.objects.filter(
            user=request.user, household=task.household
        ).exists():
            raise PermissionDenied
        task.mark_done()
        messages.success(request, f"Marked '{task.title}' done")
        return redirect(reverse("maintenance:list") + f"?household={task.household_id}")
