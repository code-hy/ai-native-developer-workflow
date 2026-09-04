from django.urls import path

from .views import (
    HouseholdCreateView,
    HouseholdDetailView,
    HouseholdListView,
    InviteCreateView,
)

app_name = "households"

urlpatterns = [
    path("", HouseholdListView.as_view(), name="list"),
    path("new/", HouseholdCreateView.as_view(), name="create"),
    path("<int:pk>/", HouseholdDetailView.as_view(), name="detail"),
    path("<int:pk>/invite/", InviteCreateView.as_view(), name="invite"),
]

# Invite token route is at top-level /invite/<token>/ handled via core/urls, but also support /households/invite/<token>
# The core urls will include InviteAcceptView
