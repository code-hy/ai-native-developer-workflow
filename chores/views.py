from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from households.models import Household, Membership

from .forms import ChoreForm
from .models import Chore


class HouseholdMemberMixin(LoginRequiredMixin):
    household = None

    def dispatch(self, request, *args, **kwargs):
        household_id = kwargs.get("household_id") or kwargs.get("pk")
        if household_id:
            self.household = get_object_or_404(Household, pk=household_id)
            if not Membership.objects.filter(
                user=request.user, household=self.household
            ).exists():
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_household(self):
        if self.household:
            return self.household
        # try to infer from chore id
        if "chore_id" in self.kwargs:
            chore = get_object_or_404(Chore, pk=self.kwargs["chore_id"])
            if not Membership.objects.filter(
                user=self.request.user, household=chore.household
            ).exists():
                raise PermissionDenied
            return chore.household
        return None


class ChoreListView(LoginRequiredMixin, ListView):
    model = Chore
    template_name = "chores/list.html"
    context_object_name = "chores"

    def get_queryset(self):
        # household_id from query param or from URL
        household_id = self.request.GET.get("household") or self.kwargs.get(
            "household_id"
        )
        qs = Chore.objects.select_related("assignee", "household")
        if household_id:
            qs = qs.filter(household_id=household_id)
            # scoping check
            if not Membership.objects.filter(
                user=self.request.user, household_id=household_id
            ).exists():
                raise PermissionDenied
        else:
            # all chores for user's households
            household_ids = Membership.objects.filter(
                user=self.request.user
            ).values_list("household_id", flat=True)
            qs = qs.filter(household_id__in=household_ids)

        # filters
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        assignee = self.request.GET.get("assignee")
        if assignee == "me":
            qs = qs.filter(assignee=self.request.user)
        elif assignee == "pool":
            qs = qs.filter(assignee__isnull=True)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return qs.order_by("due_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # for filter UI
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )
        ctx["households"] = Household.objects.filter(id__in=household_ids)
        return ctx


class ChoreCreateView(HouseholdMemberMixin, CreateView):
    model = Chore
    form_class = ChoreForm
    template_name = "chores/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["household"] = self.household
        return kwargs

    def form_valid(self, form):
        form.instance.household = self.household
        form.instance.created_by = self.request.user
        # if assignee empty, it's pool
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("chores:list") + f"?household={self.household.pk}"


class ChoreUpdateView(LoginRequiredMixin, UpdateView):
    model = Chore
    form_class = ChoreForm
    template_name = "chores/form.html"
    pk_url_kwarg = "chore_id"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["household"] = self.object.household
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        chore = get_object_or_404(Chore, pk=kwargs["chore_id"])
        if not Membership.objects.filter(
            user=request.user, household=chore.household
        ).exists():
            raise PermissionDenied
        # child cannot delete but can update? For #3 allow any member to update
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("chores:list") + f"?household={self.object.household.pk}"


class ChoreCompleteView(LoginRequiredMixin, View):
    def post(self, request, chore_id):
        chore = get_object_or_404(Chore, pk=chore_id)
        if not Membership.objects.filter(
            user=request.user, household=chore.household
        ).exists():
            raise PermissionDenied
        try:
            chore.mark_completed()
            messages.success(request, f"Chore '{chore.title}' completed")
        except ValueError as e:
            messages.error(request, str(e))
            return redirect(reverse("chores:list") + f"?household={chore.household.pk}")
        return redirect(reverse("chores:list") + f"?household={chore.household.pk}")

    def get(self, request, chore_id):
        # allow GET for HTMX convenience, but prefer POST
        return self.post(request, chore_id)


class ChoreClaimView(LoginRequiredMixin, View):
    def post(self, request, chore_id):
        chore = get_object_or_404(Chore, pk=chore_id)
        if not Membership.objects.filter(
            user=request.user, household=chore.household
        ).exists():
            raise PermissionDenied
        if chore.assignee is not None:
            messages.error(request, "Already assigned")
            return redirect(reverse("chores:list") + f"?household={chore.household.pk}")
        if chore.status != Chore.Status.TODO:
            messages.error(request, "Can only claim todo chores")
            return redirect(reverse("chores:list") + f"?household={chore.household.pk}")
        chore.assignee = request.user
        chore.save(update_fields=["assignee", "updated_at"])
        messages.success(request, f"Claimed '{chore.title}'")
        return redirect(reverse("chores:list") + f"?household={chore.household.pk}")


class ChoreDeleteView(LoginRequiredMixin, View):
    def post(self, request, chore_id):
        chore = get_object_or_404(Chore, pk=chore_id)
        if not Membership.objects.filter(
            user=request.user, household=chore.household
        ).exists():
            raise PermissionDenied
        membership = Membership.objects.get(
            user=request.user, household=chore.household
        )
        if membership.role == Membership.Role.CHILD:
            raise PermissionDenied("Children cannot delete chores")
        household_id = chore.household.pk
        chore.delete()
        messages.success(request, "Chore deleted")
        return redirect(reverse("chores:list") + f"?household={household_id}")


def ical_feed(request):
    from django.http import HttpResponse

    from chores.models import Chore
    from households.models import Membership

    if not request.user.is_authenticated:
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden()
    household_ids = Membership.objects.filter(user=request.user).values_list(
        "household_id", flat=True
    )
    chores = Chore.objects.filter(
        household_id__in=household_ids, status=Chore.Status.TODO
    ).order_by("due_at")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Household//Chores//EN",
    ]
    for c in chores:
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:chore-{c.pk}@household",
                f"DTSTAMP:{c.due_at.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{c.due_at.strftime('%Y%m%dT%H%M%SZ')}",
                f"SUMMARY:{c.title}",
                f"DESCRIPTION:{c.description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return HttpResponse("\r\n".join(lines), content_type="text/calendar")
