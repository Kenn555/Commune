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
from administration.forms import StaffForm, UserForm
from administration.models import Application, Role, Service, Staff
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
        "staff": Staff.objects.all(),
        "user": User.objects.all(),
        "application": Application.objects.all(),
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
    role_data = Role.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        role_data = role_data.filter(
                    Q(staff__first_name__icontains=request.GET['q']) |
                    Q(staff__last_name__icontains=request.GET['q'])
                )

    # Ordre
    role_data = role_data.order_by("pk").reverse()

    # Pagination
    staff_bypage = Paginator(role_data, line_bypage)

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
            "headers": [_("number"), _("full name"), _("title"), _("gender"), _("age"), _("birthday"), _("contacts"), _("status"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": role.pk,
                    "row": [
                        {"header": "number", "value": str(role.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(role.pk).zfill(9)},
                        {"header": "full name", "value": role.staff, "style": "text-start w-4 text-nowrap", "title": role.staff},
                        {"header": "title", "value": role.title, "style": "text-start w-4 text-nowrap", "title": role.title},
                        {"header": "gender", "value": Staff.GENDER_CHOICES[role.staff.gender], "style": "text-center text-nowrap", "title": Staff.GENDER_CHOICES[role.staff.gender]},
                        {"header": "age", "value": date.today().year - role.staff.birthday.year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - role.staff.birthday.year) % {"age": date.today().year - role.staff.birthday.year}},
                        {"header": "date", "value": role.staff.birthday, "style": "text-start w-4 text-nowrap", "title": role.staff.birthday},
                        {"header": "contact", "value": role.staff.contact_1 + '/' + role.staff.contact_2 if role.staff.contact_2 else role.staff.contact_1, "style": "text-start w-4 text-nowrap", "title": role.staff.contact_1 + '/' + role.staff.contact_2 if role.staff.contact_2 else role.staff.contact_1},
                        {"header": "status", "value": "✅" if role.access.is_active else "❌", "style": "text-center w-4 text-nowrap", "title": "Is active" if role.access.is_active else "Is not active"},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("open"), "url": "civil:certificate-print", "style": "green"},
                            {"name": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, role in enumerate(staff_bypage.get_page(1))
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

    menu_name = "staff"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": StaffForm(),
        "save_url": "administration:staff-save",
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
def staff_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "staff"
    
    print(request.POST.keys())
        
    form = StaffForm(request.POST)

    if form.data:
        # Table Utilisateur

        print(form.errors)

        # Table BirthCertificate
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    first_name = form['first_name'].data,
                    last_name = form['last_name'].data,
                    email = form['email'].data,
                    username = form['username'].data,
                    password = form['password'].data,
                    is_staff = True
                )
            except django.db.utils.IntegrityError:
                user = User.objects.get(
                    first_name = form['first_name'].data,
                    last_name = form['last_name'].data,
                    email = form['email'].data,
                    username = form['username'].data,
                )
            try:
                staff = Staff.objects.create(
                    first_name = form['first_name'].data,
                    last_name = form['last_name'].data,
                    gender = form['gender'].data,
                    birthday = form['birthday'].data,
                    contact_1 = form['contact_1'].data,
                    contact_2 = form['contact_2'].data,
                )
            except django.db.utils.IntegrityError:
                staff = Staff.objects.filter(
                    first_name = form['first_name'].data,
                    last_name = form['last_name'].data,
                    gender = form['gender'].data,
                    birthday = form['birthday'].data,
                    contact_1 = form['contact_1'].data,
                    contact_2 = form['contact_2'].data,
                )

            Role.objects.create(
                name = form['title'].data.lower(),
                title = form['title'].data,
                description = form['description'].data,
                app = Application.objects.get(pk=form['application'].data),
                service = Service.objects.get(pk=form['service'].data),
                staff = staff,
                access = user,
                is_boss = form['is_boss'].data,
            )

            return redirect(__package__+':'+menu_name)
        else:
            return redirect(__package__+':'+menu_name+'-register')
            

@login_required
def user_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "user"
    
    add_action_url(__package__, menu_name)
    
    print(actions)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    user_data = User.objects.filter(is_superuser=False)

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
            "headers": [_("number"), _("full name"), _("username"), _("password"), _("email"), _("staff"), _("status"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": user.pk,
                    "row": [
                        {"header": "number", "value": str(user.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(user.pk).zfill(9)},
                        {"header": "full name", "value": user.get_full_name(), "style": "text-start w-4 text-nowrap", "title": user.get_full_name()},
                        {"header": "username", "value": user.username, "style": "text-center text-nowrap", "title": user.username},
                        {"header": "password", "value": "************", "style": "text-center text-nowrap", "title": _("Password")},
                        {"header": "password", "value": user.email, "style": "text-center text-nowrap", "title": user.email},
                        {"header": "password", "value": "✅" if user.is_staff else "❌", "style": "text-center text-nowrap", "title": _("Is a staff") if user.is_staff else _("Is not a staff")},
                        {"header": "password", "value": "✅" if user.is_active else "❌", "style": "text-center text-nowrap", "title": _("Is active") if user.is_active else _("Is not a active")},
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
        "save_url": "administration:user-save",
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