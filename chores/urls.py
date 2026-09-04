from django.urls import path

from .views import (
    ChoreClaimView,
    ChoreCompleteView,
    ChoreCreateView,
    ChoreDeleteView,
    ChoreListView,
    ChoreUpdateView,
    ical_feed,
)

app_name = "chores"

urlpatterns = [
    path("", ChoreListView.as_view(), name="list"),
    path("ical/", ical_feed, name="ical"),
    path("household/<int:household_id>/new/", ChoreCreateView.as_view(), name="create"),
    path("<int:chore_id>/edit/", ChoreUpdateView.as_view(), name="edit"),
    path("<int:chore_id>/complete/", ChoreCompleteView.as_view(), name="complete"),
    path("<int:chore_id>/claim/", ChoreClaimView.as_view(), name="claim"),
    path("<int:chore_id>/delete/", ChoreDeleteView.as_view(), name="delete"),
]
