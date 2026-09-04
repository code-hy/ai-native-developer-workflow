from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView

from chores.models import Chore
from households.models import Membership


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        household_ids = Membership.objects.filter(user=user).values_list(
            "household_id", flat=True
        )
        chores = Chore.objects.filter(household_id__in=household_ids)
        now = timezone.now()
        today = now.date()
        # overdue: due_at < now and not completed
        overdue = chores.filter(due_at__lt=now).exclude(status=Chore.Status.COMPLETED)
        due_today = chores.filter(due_at__date=today).exclude(
            status=Chore.Status.COMPLETED
        )
        my_queue = chores.filter(assignee=user).exclude(status=Chore.Status.COMPLETED)
        ctx["overdue_count"] = overdue.count()
        ctx["due_today_count"] = due_today.count()
        ctx["my_queue_count"] = my_queue.count()
        ctx["households"] = Membership.objects.filter(user=user).select_related(
            "household"
        )
        # fairness teaser: last 30 days
        from chores.models import Chore as C

        since = now - timedelta(days=30)
        # compute per member effort
        # we need to show for first household if exists
        first_household_id = (
            household_ids.first() if hasattr(household_ids, "first") else None
        )
        if first_household_id is None:
            try:
                first_household_id = list(household_ids)[0]
            except IndexError:
                first_household_id = None
        if first_household_id:
            members = Membership.objects.filter(
                household_id=first_household_id
            ).select_related("user")
            total = 0
            fairness = []
            for m in members:
                pts = (
                    C.objects.filter(
                        household_id=first_household_id,
                        assignee=m.user,
                        status=C.Status.COMPLETED,
                        completed_at__gte=since,
                    ).aggregate(s=Sum("effort"))["s"]
                    or 0
                )
                fairness.append({"user": m.user, "points": pts})
                total += pts
            for f in fairness:
                f["pct"] = int(f["points"] / total * 100) if total else 0
            ctx["fairness"] = fairness
            ctx["fairness_total"] = total
        else:
            ctx["fairness"] = []
        return ctx
