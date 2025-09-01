from django.urls import path

from mines import views


app_name = "mines"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
]
