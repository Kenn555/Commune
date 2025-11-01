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
    path("staff/stop/<int:pk>", views.staff_stop, name="staff-stop"),
    # Utilisateurs
    path("user/", views.user_list, name="user"),
    path("user/register/", views.user_register, name="user-register"),
    path("user/save/", views.user_save, name="user-save"),
    # Applications
    path("role/", views.role_list, name="role"),
    path("role/save", views.role_save, name="role-save"),
    # Paramètrages
    path("settings/", views.staff_list, name="settings"),

    # URL pour récupérer les détails d'un personnel
    path('api/staff/<int:staff_id>/', views.get_staff_details, name='staff-details'),
    path('api/search_staff/<str:q_name>/', views.search_staffs, name='search-staff'),
]
