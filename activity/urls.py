import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path

from households.models import Membership

from .models import Activity
from .views import ActivityListView

app_name = "activity"


@login_required
def export_csv(request):
    household_ids = Membership.objects.filter(user=request.user).values_list(
        "household_id", flat=True
    )
    activities = Activity.objects.filter(household_id__in=household_ids).order_by(
        "-created_at"
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="activity.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["household", "actor", "action", "entity_type", "entity_id", "created_at"]
    )
    for a in activities:
        writer.writerow(
            [
                a.household_id,
                a.actor_id,
                a.action,
                a.entity_type,
                a.entity_id,
                a.created_at.isoformat(),
            ]
        )
    return response


urlpatterns = [
    path("", ActivityListView.as_view(), name="list"),
    path("export.csv", export_csv, name="export"),
]
