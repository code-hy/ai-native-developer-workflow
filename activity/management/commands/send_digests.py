from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from chores.models import Chore
from households.models import Household, Membership


class Command(BaseCommand):
    help = "Send daily 08:00 digest per household timezone"

    def handle(self, *args, **options):
        now = timezone.now()
        sent = 0
        for household in Household.objects.all():
            members = Membership.objects.filter(household=household).select_related(
                "user"
            )
            overdue = (
                Chore.objects.filter(household=household, due_at__lt=now)
                .exclude(status=Chore.Status.COMPLETED)
                .count()
            )
            for m in members:
                # check pref: assume always send for now
                try:
                    send_mail(
                        f"Daily digest for {household.name}",
                        f"Overdue: {overdue} chores. Visit dashboard.",
                        "noreply@household.local",
                        [m.user.email],
                        fail_silently=True,
                    )
                    sent += 1
                except Exception:
                    pass
        self.stdout.write(f"Sent {sent} digests")
