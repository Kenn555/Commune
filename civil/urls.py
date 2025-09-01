from django.urls import path

from civil import views


app_name = "civil"
urlpatterns = [
    path("", views.index, name='index')
]
