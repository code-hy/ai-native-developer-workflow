from django.urls import path

from .views import GroceryAddView, GroceryListView, GroceryToggleView

app_name = "groceries"
urlpatterns = [
    path("", GroceryListView.as_view(), name="list"),
    path("add/", GroceryAddView.as_view(), name="add"),
    path("<int:pk>/toggle/", GroceryToggleView.as_view(), name="toggle"),
]
