from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from households.models import Household, Membership

from .models import GroceryItem


class GroceryListView(LoginRequiredMixin, ListView):
    model = GroceryItem
    template_name = "groceries/list.html"
    context_object_name = "items"

    def get_queryset(self):
        household_id = self.request.GET.get("household")
        if household_id:
            try:
                household_id_int = int(household_id)
            except (ValueError, TypeError):
                household_id_int = household_id
            if not Membership.objects.filter(
                user=self.request.user, household_id=household_id_int
            ).exists():
                raise PermissionDenied
            return GroceryItem.objects.filter(household_id=household_id_int)
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )
        return GroceryItem.objects.filter(household_id__in=household_ids)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )

        ctx["households"] = Household.objects.filter(id__in=household_ids)
        return ctx


class GroceryAddView(LoginRequiredMixin, View):
    def post(self, request):
        household_id = request.POST.get("household")
        name = request.POST.get("name", "").strip()
        qty = request.POST.get("qty", "1").strip()
        if not household_id or not name:
            messages.error(request, "Household and name required")
            return redirect(reverse("groceries:list"))
        if not Membership.objects.filter(
            user=request.user, household_id=household_id
        ).exists():
            raise PermissionDenied
        GroceryItem.objects.create(
            household_id=household_id, name=name, qty=qty, added_by=request.user
        )
        return redirect(reverse("groceries:list") + f"?household={household_id}")


class GroceryToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(GroceryItem, pk=pk)
        if not Membership.objects.filter(
            user=request.user, household=item.household
        ).exists():
            raise PermissionDenied
        item.checked = not item.checked
        item.checked_by = request.user if item.checked else None
        item.save(update_fields=["checked", "checked_by", "updated_at"])
        return redirect(reverse("groceries:list") + f"?household={item.household_id}")
