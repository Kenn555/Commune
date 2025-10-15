from datetime import date
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from CommonAdmin.settings import COMMON_NAME
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
import django.db.utils
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.db.models import Q
from django.core.paginator import Paginator

from account.models import User
from administration.forms import UserForm
from administration.models import Staff
from civil.models import BirthCertificate
from civil.views import add_action_url, actions


# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """
    
    print(request.session['urls'])

    menu_name = "dashboard"
    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "text": [],
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])
    print(context['services'])

    return render(request, "administration/dashboard.html", context)

@login_required
def staff_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "staff"
    
    add_action_url(__package__, menu_name)
    
    print(actions)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    staff_data = Staff.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        staff_data = staff_data.filter(
                    Q(born__first_name__icontains=request.GET['q']) |
                    Q(born__last_name__icontains=request.GET['q'])
                )

    # Ordre
    staff_data = staff_data.order_by("pk").reverse()

    # Pagination
    staff_bypage = Paginator(staff_data, line_bypage)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "list",
        "actions": actions,
        "table_length": line_bypage,
        "table": {
            "headers": [_("number"), _("full name"), _("gender"), _("age"), _("birthday"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": staff.pk,
                    "row": [
                        {"header": "number", "value": str(staff.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(staff.pk).zfill(9)},
                        {"header": "full name", "value": staff.full_name, "style": "text-start w-4 text-nowrap", "title": staff.full_name},
                        {"header": "gender", "value": Staff.GENDER_CHOICES[staff.gender], "style": "text-center text-nowrap", "title": Staff.GENDER_CHOICES[staff.gender]},
                        {"header": "age", "value": date.today().year - staff.birthday.year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - staff.birthday.year) % {"age": date.today().year - staff.birthday.year}},
                        {"header": "date", "value": staff.birthday, "style": "text-start w-4 text-nowrap", "title": staff.birthday},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("open"), "url": "civil:certificate-print", "style": "green"},
                            {"name": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, staff in enumerate(staff_bypage.get_page(1))
            ],
        }
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "administration/user_list.html", context)

@login_required
def staff_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

@login_required
def user_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "user"
    
    add_action_url(__package__, menu_name)
    
    print(actions)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    user_data = User.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        user_data = user_data.filter(
                    Q(first_name__icontains=request.GET['q']) |
                    Q(last_name__icontains=request.GET['q'])
                )

    # Ordre
    user_data = user_data.order_by("pk").reverse()

    # Pagination
    user_bypage = Paginator(user_data, line_bypage)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "list",
        "actions": actions,
        "table_length": line_bypage,
        "table": {
            "headers": [_("number"), _("full name"), _("username"), _("password"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": user.pk,
                    "row": [
                        {"header": "number", "value": str(user.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(user.pk).zfill(9)},
                        {"header": "full name", "value": user.get_full_name(), "style": "text-start w-4 text-nowrap", "title": user.get_full_name()},
                        {"header": "username", "value": user.username, "style": "text-center text-nowrap", "title": user.username},
                        {"header": "password", "value": user.password, "style": "text-center text-nowrap", "title": user.password},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("modify"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, user in enumerate(user_bypage.get_page(1))
            ],
        }
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "administration/user_list.html", context)

@login_required
def user_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "user"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": UserForm(),
        "register_manager": __package__ + ":register_manager",
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "actions": actions
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "administration/user_register.html", context)

@login_required
def user_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "user"
    
    print(request.POST.keys())
        
    form = UserForm(request.POST)
    user_datas = form.fieldsets_fields[_('Informations')]
    user_datas += form.fieldsets_fields[_('Logins')]

    if form.data:
        # Table Utilisateur

        print(form.errors)

        # Table BirthCertificate
        if form.is_valid():
            user = User.objects.create_user(
                first_name = form['first_name'].data,
                last_name = form['last_name'].data,
                email = form['email'].data,
                username = form['username'].data,
                password = form['password'].data,
            )

            print(f"L'utilisateur {user.username} a été créé !!!!!!!")

            return redirect(__package__+':'+menu_name)
        else:
            return redirect(__package__+':'+menu_name+'-register')