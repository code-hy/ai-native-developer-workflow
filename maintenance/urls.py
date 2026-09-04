from django.urls import path

from .views import MaintenanceDoneView, MaintenanceListView

app_name = "maintenance"
urlpatterns = [
    path("", MaintenanceListView.as_view(), name="list"),
    path("<int:pk>/done/", MaintenanceDoneView.as_view(), name="done"),
]
