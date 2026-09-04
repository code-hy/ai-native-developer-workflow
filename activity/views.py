from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from households.models import Membership

from .models import Activity


class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = "activity/list.html"
    context_object_name = "activities"
    paginate_by = 50

    def get_queryset(self):
        household_ids = Membership.objects.filter(user=self.request.user).values_list(
            "household_id", flat=True
        )
        return Activity.objects.filter(household_id__in=household_ids).order_by(
            "-created_at"
        )[:50]


def export_csv(request):
    # wrapper for function view; use mixin logic via decorator
    pass
