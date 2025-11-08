from datetime import date, datetime, timedelta, timezone
from functools import wraps
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
from CommonAdmin.settings import COMMON_NAME
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
import django.db.utils
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.contrib import messages

from account.models import User
from administration.forms import RoleForm, StaffForm, UserForm
from administration.models import Application, Role, Service, Staff
from civil.models import BirthCertificate
from civil.views import add_action_url, actions


TIMEZONE_MGA = timezone(timedelta(hours=3))
TIMEZONE_UTC = timezone(timedelta(hours=0))

@login_required
def search_staffs(request, q_name:str):
    """Retourne une liste de personnes en JSON"""
    try:
        staff_list = Staff.objects.filter(
            Q(last_name__icontains=q_name) | Q(first_name__icontains=q_name),
        )

        data = {
            "staff_list": [staff.pk for staff in staff_list],
        }

        data['staff_name'] = {}

        for staff in staff_list:
            data['staff_name'][staff.pk] = staff.full_name + ' born at ' + staff.birthday.astimezone(TIMEZONE_MGA).__format__('%d-%m-%Y %H:%M') 
        
        return JsonResponse(data)
    except Staff.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    ...

@login_required 
def get_staff_details(request, staff_id):
    """Retourne les détails d'une personne en JSON"""
    try:
        staff = Staff.objects.get(id=staff_id)
        
        data = {
            'fields': [
                staff.last_name,
                staff.first_name,
                staff.gender,
            ]
        }

        data = {
            "last_name": staff.last_name,
            "first_name": staff.first_name,
            "gender": staff.gender,
        }

        data["birthday"] = staff.birthday.astimezone(TIMEZONE_MGA).strftime('%Y-%m-%dT%H:%M')

        print(data)
        
        return JsonResponse(data)
    except Staff.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    
# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """
    
    menu_name = "dashboard"

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "text": [],
        "staff": Staff.objects.all(),
        "user": User.objects.all(),
        "role": Role.objects.all(),
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "administration/dashboard.html", context)

@login_required
def staff_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "staff"
    
    add_action_url(__package__, menu_name)
    
    print(actions)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    staff = Staff.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        staff = staff.filter(
                    Q(first_name__icontains=request.GET['q']) |
                    Q(last_name__icontains=request.GET['q'])
                )

    # Ordre
    staff = staff.order_by("role_id", "is_active").reverse()

    # Pagination
    staff_bypage = Paginator(staff, line_bypage)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
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
            "headers": [_("number"), _("full name"), _("title"), _("gender"), _("age"), _("birthday"), _("contacts"), _("service"), _("status"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": staff.pk,
                    "row": [
                        {"header": "number", "value": str(staff.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(staff.pk).zfill(9)},
                        {"header": "full name", "value": staff.full_name, "style": "text-start w-4 text-nowrap", "title": staff.full_name},
                        {"header": "title", "value": staff.role or staff.last_role.__str__() + _("(before)"), "style": "text-start w-4 text-nowrap", "title": staff.role or staff.last_role.__str__() + _("(before)")},
                        {"header": "gender", "value": Staff.GENDER_CHOICES[staff.gender], "style": "text-center text-nowrap", "title": Staff.GENDER_CHOICES[staff.gender]},
                        {"header": "age", "value": date.today().year - staff.birthday.year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - staff.birthday.year) % {"age": date.today().year - staff.birthday.year}},
                        {"header": "date", "value": staff.birthday, "style": "text-start w-4 text-nowrap", "title": staff.birthday},
                        {"header": "contact", "value": staff.contact_1 + '/' + staff.contact_2 if staff.contact_2 else staff.contact_1, "style": "text-start w-4 text-nowrap", "title": staff.contact_1 + '/' + staff.contact_2 if staff.contact_2 else staff.contact_1},
                        {"header": "service", "value": staff.role.service.title.title() if staff.role else staff.last_role.service.title.title(), "style": "text-start w-4 text-nowrap", "title": staff.role.service.title.title() if staff.role else staff.last_role.service.title.title()},
                        {"header": "status", "value": "✅" if staff.role else "❌", "style": "text-center w-4 text-nowrap", "title": "Is active" if staff.role else "Is not active"},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            # {"name": _("open"), "url": __package__+":staff", "style": "green"},
                            {"name": _("stop"), "url": __package__+":staff-stop", "style": "red"}
                            if staff.role else 
                            {"name": _("affect"), "url": __package__+":staff-stop", "style": "green"},
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

    menu_name = "staff"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
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
            role = Role.objects.get(pk=form.data['title'])

            print(role)
            print(form['last_name'].data)

            if Staff.objects.filter(role=role).count() < 1:
                user = role.access

                if user:
                    user.last_name = form['last_name'].data
                    user.first_name = form['first_name'].data
                    user.username = form['username'].data
                    user.password = make_password(form['password'].data)
                else:
                    user = User(
                        last_name = form['last_name'].data,
                        first_name = form['first_name'].data,
                        username = form['username'].data,
                        password = make_password(form['password'].data),
                    )
                    role.access = user

                user.email = form['email'].data
                user.is_staff = True

                staff, staff_exists = Staff.objects.get_or_create(
                    first_name = form['first_name'].data,
                    last_name = form['last_name'].data,
                    gender = form['gender'].data,
                    birthday = form['birthday'].data,
                )
                staff.email = form['email'].data
                staff.contact_1 = form['contact_1'].data
                staff.contact_2 = form['contact_2'].data
                staff.role = role

                user.save()
                role.save()
                staff.save()
            else:
                print("Un personnel est déjà affilié à ce poste. Trouvez-en un autre !!!!")
                messages.error(request, "This role is already occupied by another staff !")

            messages.success(request, "Staff created successfully !")
            return redirect(__package__+':'+menu_name)
        else:
            messages.error(request, "Staff Creation Error !")
            return redirect(__package__+':'+menu_name+'-register')
            
@login_required
def staff_stop(request: WSGIRequest, pk:int) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "staff"

    staff = Staff.objects.get(pk=pk)
    # Changement de valeurs
    staff.is_active = False
    staff.last_role = staff.role
    staff.date_joined_last_role = staff.date_joined
    staff.date_stoped_last_role = datetime.now()
    # Mise à null de l'ancien role
    staff.role = None
    
    try:
        staff.save(update_fields=["is_active", "last_role", "date_joined_last_role", "date_stoped_last_role", "role"])
        messages.success(request, "Staff stopped successfully !")
    except:
        messages.error(request, "Staff Stop Error !")

    return redirect(__package__+':'+menu_name)

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
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
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
                        {"header": "full name", "value": user.get_full_name(), "style": "text-start w-4 text-nowrap", "title": _("It's Me") if user == request.user else user.get_full_name()},
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
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
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
            messages.success(request, "User created successfully !")

            return redirect(__package__+':'+menu_name)
        else:
            messages.error(request, "User Creation Error !")
            return redirect(__package__+':'+menu_name+'-register')

@login_required
def role_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "role"
    
    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    role = Role.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        role = role.filter(
                    Q(name__icontains=request.GET['q']) |
                    Q(title__icontains=request.GET['q'])
                )

    # Ordre
    role = role.order_by("service__grade", "grade")

    # Pagination
    role_bypage = Paginator(role, line_bypage)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "form": RoleForm(),
        "table_length": line_bypage,
        "table": {
            "headers": [_("number"), _("title"), _("date"), _("service"), _("grade"), _("app"), _("status"), _("occupant"), _("since"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": role.pk,
                    "row": [
                        {"header": "number", "value": str(role.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(role.pk).zfill(9)},
                        {"header": "title", "value": role.title, "style": "text-start w-4 text-nowrap", "title": role.title},
                        {"header": "date", "value": role.date_created, "style": "text-start w-4 text-nowrap", "title": role.date_created},
                        {"header": "service", "value": role.service.title.title(), "style": "text-center w-4 text-nowrap", "title": role.service.title.title()},
                        {"header": "grade", "value": role.grade, "style": "text-center w-4 text-nowrap", "title": role.grade},
                        {"header": "app", "value": role.app, "style": "text-center w-4 text-nowrap", "title": role.app},
                        {"header": "status", "value": "✅" if Staff.objects.filter(role=role) else "❌", "style": "text-center w-4 text-nowrap", "title": "Is active" if Staff.objects.filter(role=role) else "Is not active"},
                        {"header": "occupant", "value": Staff.objects.get(role=role).full_name if Staff.objects.filter(role=role) else "No one", "style": "text-center w-4 text-nowrap", "title": Staff.objects.get(role=role).full_name if Staff.objects.filter(role=role) else "No one"},
                        {"header": "since", "value": Staff.objects.get(role=role).since if Staff.objects.filter(role=role) else "No one", "style": "text-center w-4 text-nowrap", "title": Staff.objects.get(role=role).since if Staff.objects.filter(role=role) else "No one"},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("open"), "url": __package__+":role", "style": "green"},
                            {"name": _("delete"), "url": __package__+":role", "style": "red"},
                        ]},
                    ],
                } for index, role in enumerate(role_bypage.get_page(1))
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

    return render(request, "administration/role_list.html", context)

@login_required
def role_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "role"
    
    print(request.POST.keys())
        
    form = RoleForm(request.POST)

    # Table Poste
    if form.data and form.is_valid():
        role, role_exists = Role.objects.get_or_create(
            name = "_".join(form['title'].data.lower().split(" ")),
            title = form['title'].data,
            description = form['description'].data,
            service = Service.objects.get(pk=form['service'].data),
            grade = form['grade'].data,
            app = Application.objects.get(pk=form['application'].data),
        )


        print(f"L'utilisateur {role.name} a été créé !!!!!!!")
        messages.success(request, "User created successfully !")
    else:
        messages.error(request, "User Creation Error !")

    return redirect(__package__+':'+menu_name)
