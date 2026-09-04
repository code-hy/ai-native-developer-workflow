from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from chores.models import Chore
from households.models import Membership


def fairness_scores(household, window="month"):
    now = timezone.now()
    if window == "week":
        since = now - timedelta(days=7)
    elif window == "month":
        since = now - timedelta(days=30)
    else:
        since = now - timedelta(days=365 * 10)
    members = Membership.objects.filter(household=household).select_related("user")
    scores = {}
    for m in members:
        total = (
            Chore.objects.filter(
                household=household,
                assignee=m.user,
                status=Chore.Status.COMPLETED,
                completed_at__gte=since,
            ).aggregate(s=Sum("effort"))["s"]
            or 0
        )
        scores[m.user_id] = total
    return scores
