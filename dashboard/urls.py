from django.urls import path

from dashboard import views


app_name = "dashboard"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
]
