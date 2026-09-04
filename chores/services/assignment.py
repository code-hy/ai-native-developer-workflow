from chores.models import Chore
from households.models import Membership


def get_ordered_members(household):
    return list(
        Membership.objects.filter(household=household)
        .order_by("joined_at")
        .values_list("user_id", flat=True)
    )


def get_next_assignee(household, current_assignee_id=None):
    members = get_ordered_members(household)
    if not members:
        return None
    if current_assignee_id is None or current_assignee_id not in members:
        return members[0]
    idx = members.index(current_assignee_id)
    return members[(idx + 1) % len(members)]


def get_effort_balanced_assignee(household):
    """Return member with min sum(effort) last 30 days."""
    from datetime import timedelta

    from django.db.models import Sum
    from django.utils import timezone

    since = timezone.now() - timedelta(days=30)
    members = Membership.objects.filter(household=household)
    # compute sum per member
    scores = {}
    for m in members:
        total = (
            Chore.objects.filter(
                household=household,
                assignee=m.user,
                status=Chore.Status.COMPLETED,
                completed_at__gte=since,
            ).aggregate(total=Sum("effort"))["total"]
            or 0
        )
        scores[m.user_id] = total
    if not scores:
        return None
    # return min
    return min(scores, key=lambda k: scores[k])


def can_claim(chore: Chore, user) -> bool:
    return chore.assignee is None and chore.status == Chore.Status.TODO
