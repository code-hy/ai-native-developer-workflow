from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Chore
from core.rrule import next_due


class Command(BaseCommand):
    help = "Generate next instances for recurring chores/bills/maintenance where next due < now+7d"

    def handle(self, *args, **options):
        now = timezone.now()
        horizon = now + timezone.timedelta(days=7)
        created = 0
        # chores with rrule
        for chore in Chore.objects.filter(status=Chore.Status.COMPLETED).exclude(
            rrule=""
        ):
            # find latest completed instance's due_at as dtstart reference? Use completed chore's due_at
            # Find if there's already a todo instance with same title/household and due after this chore's due
            # Simplified: if next_due after this chore's due is within horizon and no existing todo with that due, create
            try:
                tz = ZoneInfo(chore.household.timezone or "UTC")
            except Exception:
                tz = ZoneInfo("UTC")
            dtstart = chore.due_at
            nxt = next_due(chore.rrule, chore.due_at, tz, dtstart=dtstart)
            # keep advancing until nxt > chore.due_at and nxt <= horizon
            if nxt and nxt <= horizon:
                # check duplicate: any chore with same title/household and due_at already exists (avoid re-creating old)
                exists = Chore.objects.filter(
                    household=chore.household, title=chore.title, due_at=nxt
                ).exists()
                if not exists:
                    # rotating: if chore had assignee, rotate to next member
                    next_assignee = chore.assignee
                    if chore.rrule and chore.assignee:
                        from chores.services.assignment import get_next_assignee

                        next_id = get_next_assignee(chore.household, chore.assignee_id)
                        if next_id:
                            from accounts.models import User

                            try:
                                next_assignee = User.objects.get(pk=next_id)
                            except User.DoesNotExist:
                                next_assignee = chore.assignee
                    Chore.objects.create(
                        household=chore.household,
                        title=chore.title,
                        description=chore.description,
                        category=chore.category,
                        effort=chore.effort,
                        minutes=chore.minutes,
                        status=Chore.Status.TODO,
                        assignee=next_assignee,
                        rrule=chore.rrule,
                        due_at=nxt,
                        created_by=chore.created_by,
                    )
                    created += 1
        self.stdout.write(f"Created {created} due instances")
