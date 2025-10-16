from django.urls import path

from administration import views


app_name = "administration"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
    # Personnels
    path("staff/", views.staff_list, name="staff"),
    path("staff/register/", views.staff_register, name="staff-register"),
    path("staff/save/", views.staff_save, name="staff-save"),
    # Utilisateurs
    path("user/", views.user_list, name="user"),
    path("user/register/", views.user_register, name="user-register"),
    path("user/save/", views.user_save, name="user-save"),
    # Applications
    path("app/", views.staff_list, name="application"),
    # Paramètrages
    path("settings/", views.staff_list, name="settings"),

]
