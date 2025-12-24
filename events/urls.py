from django.urls import path

from events import views


app_name = "events"

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
    path("calendar/", views.calendar_show, name="calendar"),
    path("calendar/register/", views.event_register, name="calendar-register"),
    path("calendar/<int:event_id>", views.event_details, name="event-details"),
    path("calendar/<int:event_id>/delete", views.event_delete, name="event-delete"),
    path("tasks/", views.tasks_list, name="tasks"),
    path("tasks/register/", views.tasks_register, name="tasks-register"),
]
