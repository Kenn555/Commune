from django.urls import path

from account import views


app_name = "account"
urlpatterns = [
    path("", views.index, name="index"),
    path("accounts/login/", views.login_page, name="login"),
    path("logout/", views.logout_page, name="logout"),
]
