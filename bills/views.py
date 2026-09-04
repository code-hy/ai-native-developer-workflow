from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from households.models import Membership

from .models import Bill


class BillListView(LoginRequiredMixin, ListView):
    model = Bill
    template_name = "bills/list.html"
    context_object_name = "bills"

    def get_queryset(self):
        household_id = self.request.GET.get("household")
        if household_id:
            if not Membership.objects.filter(
                user=self.request.user, household_id=household_id
            ).exists():
                raise PermissionDenied
            return Bill.objects.filter(household_id=household_id).order_by("due_at")
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )
        return Bill.objects.filter(household_id__in=household_ids).order_by("due_at")


class BillTogglePaidView(LoginRequiredMixin, View):
    def post(self, request, pk):
        bill = get_object_or_404(Bill, pk=pk)
        if not Membership.objects.filter(
            user=request.user, household=bill.household
        ).exists():
            raise PermissionDenied
        if bill.status == Bill.Status.PAID:
            bill.status = Bill.Status.DUE
            bill.paid_at = None
        else:
            bill.status = Bill.Status.PAID
            bill.paid_at = timezone.now()
            # create next if recurring (simplified)
            if bill.rrule:
                from zoneinfo import ZoneInfo

                from core.rrule import next_due

                try:
                    tz = ZoneInfo(bill.household.timezone or "UTC")
                except Exception:
                    tz = ZoneInfo("UTC")
                nxt = next_due(bill.rrule, bill.due_at, tz, dtstart=bill.due_at)
                if (
                    nxt
                    and not Bill.objects.filter(
                        household=bill.household, name=bill.name, due_at=nxt
                    ).exists()
                ):
                    # rotate payer
                    from chores.services.assignment import get_next_assignee

                    next_payer_id = (
                        get_next_assignee(bill.household, bill.payer_id)
                        if bill.payer
                        else None
                    )
                    next_payer = None
                    if next_payer_id:
                        from accounts.models import User

                        try:
                            next_payer = User.objects.get(pk=next_payer_id)
                        except User.DoesNotExist:
                            pass
                    Bill.objects.create(
                        household=bill.household,
                        name=bill.name,
                        amount=bill.amount,
                        currency=bill.currency,
                        due_at=nxt,
                        rrule=bill.rrule,
                        payer=next_payer,
                        status=Bill.Status.DUE,
                    )
        bill.save()
        messages.success(request, f"Bill '{bill.name}' toggled")
        return redirect(reverse("bills:list") + f"?household={bill.household_id}")
