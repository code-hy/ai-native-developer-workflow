from django.db.models.signals import post_save
from django.dispatch import receiver

from chores.models import Chore

from .models import Activity


@receiver(post_save, sender=Chore)
def log_chore_activity(sender, instance, created, **kwargs):
    # simple: log create vs update
    action = "created" if created else "updated"
    if instance.status == Chore.Status.COMPLETED and instance.completed_at:
        # check if this is a completion event vs regular update
        # we log completed separately if just transitioned
        action = "completed"
    Activity.objects.create(
        household=instance.household,
        actor=instance.created_by or instance.assignee,
        action=action,
        entity_type="chore",
        entity_id=instance.pk,
        diff={"title": instance.title, "status": instance.status},
    )
