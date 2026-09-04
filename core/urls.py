from django.contrib import admin
from django.urls import include, path

from core.views import DashboardView
from households.views import InviteAcceptView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("households/", include("households.urls")),
    path("chores/", include("chores.urls")),
    path("groceries/", include("groceries.urls")),
    path("bills/", include("bills.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("activity/", include("activity.urls")),
    path("invite/<str:token>/", InviteAcceptView.as_view(), name="invite-accept"),
    path("", DashboardView.as_view(), name="dashboard"),
]
