from django.urls import path

from administration import views


app_name = "administration"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
]
