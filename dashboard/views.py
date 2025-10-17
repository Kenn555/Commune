from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.conf import settings
from django.utils.translation import gettext as _


app_name = "dashboard"

# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """ 

    menu_name = "dashboard"
    context = {
        "accessed":__package__ in request.session['app_accessed'],
        "user": request.user,
        "app_name": app_name,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": []
    }

    for service in request.session['urls']:
        if service['name'] == app_name:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "dashboard/home.html", context)