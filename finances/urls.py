from django.urls import path

from finances import views


app_name = "finances"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
]
