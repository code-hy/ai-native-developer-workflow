from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("households/", include("households.urls")),
    path("chores/", include("chores.urls")),
    path("groceries/", include("groceries.urls")),
    path("bills/", include("bills.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("activity/", include("activity.urls")),
    path("", TemplateView.as_view(template_name="dashboard.html"), name="dashboard"),
]
