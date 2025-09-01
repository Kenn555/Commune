from django.urls import path

from social import views


app_name = "social"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
]
