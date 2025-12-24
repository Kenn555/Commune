import json
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from CommonAdmin.settings import COMMON_NAME
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext as _

from events.forms import EventForm, TaskForm
from events.models import Category, Event, Task


app_name = "events"

actions = [
    {
        'name': "list",
        'title': "",
        'url': ""
    },
    {
        'name': "register",
        'title': "",
        'url': ""
    },
]

# Create your views here.
def add_action_url(app, menu_name):
    for action in actions:
        if action['name'] == 'list':
            action['title'] = _("list")
            action['url'] = app + ":" + menu_name
        elif action['name'] == 'register':
            action['title'] = _("register")
            action['url'] = app + ":" + menu_name + "-register"


@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "dashboard"
    
    add_action_url(__package__, menu_name)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "action_name": "register",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
    }

    for service in request.session['urls']:
        if service['name'] == app_name:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    # return render(request, "events/dashboard.html", context)
    return redirect(__package__ + ":calendar")

@login_required
def calendar_show(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "calendar"
    
    add_action_url(__package__, menu_name)

    events = [{
        "url": event.pk,
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "description": event.description,
        "color": event.category.color,
        "textColor": event.category.text_color,
        "category": event.category.name if event.category else None,
        "isUrgent": event.is_urgent
    } for event in Event.objects.all()]
    events_json = json.dumps(events)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "action_name": "list",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "forms": EventForm(),
        "events_json": events_json,
    }    

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "events/list.html", context)

@login_required
def event_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "calendar"
    
    add_action_url(__package__, menu_name)

    if request.method == "POST":
        print("POST request received")
        form = EventForm(request.POST)
        if form.is_valid():
            Event.objects.create(
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                start = form.cleaned_data['start'],
                end = form.cleaned_data['end'],
                color = form.cleaned_data['color'],
                text_color = form.cleaned_data['text_color'],
                category = Category(pk=form.cleaned_data['category']),
                is_urgent = form.cleaned_data['is_urgent'],
            )
            
            messages.success(request, _("Event modified successfully."))
            return redirect(__package__ + ":" + menu_name)
        else:
            messages.error(request, _("Please correct the errors below."))


    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "action_name": "register",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "forms": EventForm(),
    }    

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "events/register.html", context)

@login_required
def event_details(request: WSGIRequest, event_id:int) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "calendar"

    event = get_object_or_404(Event, pk=event_id)
    forms = EventForm(initial=event.__dict__)
    forms.fields.get('category').initial = event.category.pk

    if request.method == "POST":
        print("POST request received")
        form = EventForm(request.POST)
        if form.is_valid():
            event.title = form.cleaned_data['title']
            event.description = form.cleaned_data['description']
            event.start = form.cleaned_data['start']
            event.end = form.cleaned_data['end']
            event.color = form.cleaned_data['color']
            event.text_color = form.cleaned_data['text_color']
            event.category = Category(pk=form.cleaned_data['category'])
            event.is_urgent = form.cleaned_data['is_urgent']
            # Enregistrer les modifications
            event.save()
            
            messages.success(request, _("Event modified successfully."))
        else:
            messages.error(request, _("Please correct the errors below."))


    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "forms": forms,
        "event": event,
    }
    
    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "events/details.html", context)

@login_required
def event_delete(request: WSGIRequest, event_id:int) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    Event.objects.get(pk=event_id).delete()

    messages.success(request, _("Event deleted successfully."))

    return redirect(__package__+":calendar")

@login_required    
def tasks_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "tasks"
    
    add_action_url(__package__, menu_name)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "action_name": "list",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
    }
    
    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "events/list.html", context)

@login_required    
def tasks_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "tasks"
    
    add_action_url(__package__, menu_name)

    if request.method == "POST":
        print("POST request received")
        form = TaskForm(request.POST)
        if form.is_valid():
            Task.objects.create(
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                due_date=form.cleaned_data['due_date'],
                event=Event(pk=form.cleaned_data['event']),
                priority=form.cleaned_data['priority'],
            )
            messages.success(request, _("Event added successfully."))
            return redirect(__package__ + ":calendar")
        else:
            messages.error(request, _("Please correct the errors below."))

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "actions": actions,
        "action_name": "register",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "forms": TaskForm(),
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "events/register.html", context)