from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from .forms import HouseholdForm, InviteForm
from .models import Household, Invite, Membership


class HouseholdMembershipRequiredMixin(LoginRequiredMixin):
    household = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        household_id = kwargs.get("pk") or kwargs.get("household_id")
        if household_id:
            self.household = get_object_or_404(Household, pk=household_id)
            if not Membership.objects.filter(
                user=request.user, household=self.household
            ).exists():
                raise PermissionDenied("Not a member of this household")
        return super().dispatch(request, *args, **kwargs)


class HouseholdCreateView(LoginRequiredMixin, CreateView):
    model = Household
    form_class = HouseholdForm
    template_name = "households/create.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # create membership admin
        Membership.objects.create(
            user=self.request.user, household=self.object, role=Membership.Role.ADMIN
        )
        messages.success(self.request, f"Household '{self.object.name}' created.")
        return response

    def get_success_url(self):
        return reverse("households:detail", kwargs={"pk": self.object.pk})


class HouseholdListView(LoginRequiredMixin, ListView):
    model = Household
    template_name = "households/list.html"
    context_object_name = "households"

    def get_queryset(self):
        return Household.objects.filter(memberships__user=self.request.user).distinct()


class HouseholdDetailView(HouseholdMembershipRequiredMixin, DetailView):
    model = Household
    template_name = "households/detail.html"
    context_object_name = "household"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["memberships"] = Membership.objects.filter(
            household=self.object
        ).select_related("user")
        ctx["invite_form"] = InviteForm()
        ctx["invites"] = Invite.objects.filter(
            household=self.object, accepted_at__isnull=True
        ).order_by("-created_at")[:10]
        # check if current user is admin
        try:
            membership = Membership.objects.get(
                user=self.request.user, household=self.object
            )
            ctx["is_admin"] = membership.role == Membership.Role.ADMIN
            ctx["current_role"] = membership.role
        except Membership.DoesNotExist:
            ctx["is_admin"] = False
        return ctx


class InviteCreateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        household = get_object_or_404(Household, pk=pk)
        # membership check
        if not Membership.objects.filter(
            user=request.user, household=household
        ).exists():
            raise PermissionDenied
        # disallow child role to invite
        membership = Membership.objects.get(user=request.user, household=household)
        if membership.role == Membership.Role.CHILD:
            raise PermissionDenied("Children cannot invite")
        form = InviteForm(request.POST)
        if form.is_valid():
            invite = form.save(commit=False)
            invite.household = household
            invite.created_by = request.user
            invite.save()
            messages.success(request, f"Invite sent to {invite.email}")
        else:
            messages.error(request, f"Invite error: {form.errors.as_text()}")
        return redirect("households:detail", pk=household.pk)


class InviteAcceptView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        invite = get_object_or_404(Invite, token=token)
        if invite.is_expired():
            return HttpResponse("Invite expired", status=410)
        if invite.accepted_at is not None:
            return HttpResponse("Invite already accepted", status=410)

        # If not logged in, redirect to signup with next
        if not request.user.is_authenticated:
            # store token in session to auto-join after signup/login
            request.session["pending_invite_token"] = token
            messages.info(
                request, f"Please sign up or log in to accept invite for {invite.email}"
            )
            return redirect(f"/accounts/signup/?next=/invite/{token}/")

        # Logged in user: check email matches? Allow any authenticated user to accept but prefer matching email
        # Create membership if not already member
        if Membership.objects.filter(
            user=request.user, household=invite.household
        ).exists():
            messages.info(request, "You are already a member of this household")
            return redirect("households:detail", pk=invite.household.pk)

        Membership.objects.create(
            user=request.user, household=invite.household, role=invite.role
        )
        invite.accepted_at = timezone.now()
        invite.accepted_by = request.user
        invite.save(update_fields=["accepted_at", "accepted_by"])
        messages.success(request, f"Joined household '{invite.household.name}'")
        return redirect("households:detail", pk=invite.household.pk)

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        # same as GET for form POST
        return self.get(request, token)
