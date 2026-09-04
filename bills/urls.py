from django.urls import path

from .views import BillListView, BillTogglePaidView

app_name = "bills"
urlpatterns = [
    path("", BillListView.as_view(), name="list"),
    path("<int:pk>/toggle/", BillTogglePaidView.as_view(), name="toggle"),
]
