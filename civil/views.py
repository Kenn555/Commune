from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from itertools import chain
import json
from operator import attrgetter
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, DeleteView
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncYear, TruncMonth

import django.db.utils
from administration.models import Fokotany, Role, Staff
from django.db.models import Q
from civil import forms
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import ngettext, get_language
from dal import autocomplete
from babel.dates import format_date

from civil.forms import BirthCertificateForm, DeathCertificateForm, MarriageCertificateForm, PersonForm
from civil.models import BirthCertificate, BirthCertificateDocument, DeathCertificate, DeathCertificateDocument, MarriageCertificate, Person
from civil.templatetags.isa_gasy import VolanaGasy
from finances.models import ServicePrice


CERTIFICATE = {
    "person": PersonForm,
    "birth": BirthCertificateForm,
    "death": DeathCertificateForm,
    "marriage": MarriageCertificateForm,
}

GENDER_CHOICES = {
    'M': _("Male"),
    'F': _("Female")
}

GENDER_CLIENT = {
    'M': "Atoa",
    'F': "Rtoa"
}

TIMEZONE_MGA = timezone(timedelta(hours=3))
TIMEZONE_UTC = timezone(timedelta(hours=0))

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

def date_translate(month_year:datetime):
    if get_language() == 'mg':
        return f"{VolanaGasy(month_year.month).ho_teny()} {month_year.year}".capitalize()
    elif get_language() == 'fr':
        return format_date(month_year, format='MMMM yyyy', locale='fr_FR').capitalize()
    else:
        return format_date(month_year, format='MMMM yyyy', locale='en_US').capitalize()


def add_action_url(app, menu_name):
    for action in actions:
        if action['name'] == 'list':
            action['title'] = _("list")
            action['url'] = app + ":" + menu_name
        elif action['name'] == 'register':
            action['title'] = _("register")
            action['url'] = app + ":" + menu_name + "-register"

class PersonAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete pour rechercher des personnes existantes"""
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Person.objects.none()

        qs = Person.objects.filter(birthday__lte=date.today() - timedelta(days=18*365))

        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )

        return qs.order_by('last_name', 'first_name')

    def get_result_label(self, item):
        """Format d'affichage dans la liste déroulante"""
        return _("%(last_name)s %(first_name)s - person at %(birthday_day)s at %(birthday_hour)s.") % {
            "last_name": item.last_name, 
            "first_name": item.first_name, 
            "birthday_day": item.birthday.astimezone(TIMEZONE_MGA).strftime('%d/%m/%Y'),
            "birthday_hour": item.birthday.astimezone(TIMEZONE_MGA).strftime('%H:%M')
        }


class FatherAutocomplete(PersonAutocomplete):
    """Autocomplete spécifique pour les pères"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        print(qs)
        return qs.filter(gender='M')


class MotherAutocomplete(PersonAutocomplete):
    """Autocomplete spécifique pour les mères"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(gender='F')

@login_required
def search_persons(request: WSGIRequest, type:str, q_name:str):
    """Retourne une liste de personnes en JSON"""
    try:
        person_list = Person.objects.filter(
            Q(last_name__icontains=q_name) | Q(first_name__icontains=q_name)
        )

        if type == 'M':
            person_list = person_list.filter(gender='M', birthday__lte=date.today() - timedelta(days=18*365))
        elif type == 'F':
            person_list = person_list.filter(gender='F', birthday__lte=date.today() - timedelta(days=18*365))

        data = {
            "person_list": [person.pk for person in person_list],
        }

        data['person_name'] = {}

        for person in person_list:
            try:
                data['person_name'][person.pk] = person.full_name + ' person at ' + person.birthday.astimezone(TIMEZONE_MGA).__format__('%d-%m-%Y %H:%M') 
            except OSError:
                data['person_name'][person.pk] = person.full_name + ' person at ' + (person.birthday + timedelta(hours=3)).__format__('%d-%m-%Y %H:%M') 
        
        return JsonResponse(data)
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    ...

@login_required 
def get_person_details(request: WSGIRequest, person_id):
    """Retourne les détails d'une personne en JSON"""
    try:
        person = Person.objects.get(id=person_id)

        data = {
            "last_name": person.last_name,
            "first_name": person.first_name,
            "gender": person.gender,
            "birth_place": person.birth_place,
            "carreer": person.carreer,
            "address": person.address,
        }
        try:
            data["birthday"] = person.birthday.astimezone(TIMEZONE_MGA).strftime('%Y-%m-%dT%H:%M')
        except OSError:
            data["birthday"] = (person.birthday + timedelta(hours=3)).__format__('%Y-%m-%dT%H:%M')

        print(data)
        
        return JsonResponse(data)
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    
# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "dashboard"


    year_selected = int(request.GET.get('year', datetime.now().year))

    year__first_day = datetime(year_selected, 1, 1)
    year__last_day = datetime(year_selected, 12, 31)

    fokotany = Fokotany.objects.all()
    births = BirthCertificate.objects.all()
    deaths = DeathCertificate.objects.all()
    marriages = MarriageCertificate.objects.all()

    years_qr = BirthCertificate.objects.annotate(year=TruncYear('person__birthday', tzinfo=TIMEZONE_UTC)).values_list('year').order_by('year').reverse()

    years = [datetime.now().year]

    for year in years_qr:
        if not year[0].year in years:
            years.append(year[0].year)

    # years.reverse()

    births_this_year = births.filter(
        person__birthday__gte=year__first_day,
        person__birthday__lte=year__last_day,
    )
    deaths_this_year = deaths.filter(
        death_day__gte=year__first_day,
        death_day__lte=year__last_day,
    )
    marriages_this_year = marriages.filter(
        date_created__gte=year__first_day,
        date_created__lte=year__last_day,
    )

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
        "birth_count": BirthCertificate.objects.count(),
        "death_count": DeathCertificate.objects.count(),
        "fkt_name": json.dumps({'fokotany': [fkt.name for fkt in fokotany]}),
        "fokotany": [fkt for fkt in fokotany],
        "years": years,
        "year_selected": year_selected,
        "certificates_year__count": sum([
            births_this_year.count(), 
            deaths_this_year.count(),
            marriages_this_year.count(),
        ]),
    }

    # print(year__first_day)

    births_by_month = births_this_year.annotate(
        month=TruncMonth('person__birthday', tzinfo=TIMEZONE_UTC)
    ).values('month').annotate(
        count=Count('month')
    ).order_by('month')

    deaths_by_month = deaths_this_year.annotate(
        month=TruncMonth('death_day', tzinfo=TIMEZONE_UTC)
    ).values('month').annotate(
        count=Count('month')
    ).order_by('month')

    marriages_by_month = marriages_this_year.annotate(
        month=TruncMonth('wedding_day', tzinfo=TIMEZONE_UTC)
    ).values('month').annotate(
        count=Count('month')
    ).order_by('month')

    birth_dict = {birth['month'].astimezone(TIMEZONE_MGA).strftime('%Y-%m'): birth['count'] for birth in births_by_month}
    death_dict = {death['month'].astimezone(TIMEZONE_MGA).strftime('%Y-%m'): death['count'] for death in deaths_by_month}
    marriage_dict = {marriage['month'].astimezone(TIMEZONE_MGA).strftime('%Y-%m'): marriage['count'] for marriage in marriages_by_month}

    all_months = sorted(set(birth_dict.keys()) | set(death_dict.keys()) | set(marriage_dict.keys()))

    # print(birth_dict)
    # print(death_dict)
    # print(all_months)

    formatted_births = []
    formatted_deaths = []
    formatted_marriages = []

    for month_str in all_months:
        birth_month = birth_dict.get(month_str, Decimal('0'))
        death_month = death_dict.get(month_str, Decimal('0'))
        marriage_month = marriage_dict.get(month_str, Decimal('0'))
        
        # Convertir la chaîne de date en objet datetime pour le formatage
        month_date = datetime.strptime(month_str, '%Y-%m')

        formatted_births.append({
            'month': month_date,
            'total': float(birth_month)  # Convertir en float pour JSON
        })
        formatted_deaths.append({
            'month':  month_date,
            'total': float(death_month)  # Convertir en float pour JSON
        })
        formatted_marriages.append({
            'month':  month_date,
            'total': float(marriage_month)  # Convertir en float pour JSON
        })

    # print(formatted_births)
    # print(formatted_deaths)

    certificates_year = {
        "labels": [ date_translate(birth['month']) for birth in formatted_births],
        "datasets": [
            {
                'label': _("birth certificate").capitalize() + '~' + str(births_this_year.count()),
                'data': [birth['total'] for birth in formatted_births],
                'backgroundColor': "#5697ff",
                'borderColor': '#5697ff',
                'borderRadius': 50,
            },
            {
                'label': _("death certificate").capitalize() + '~' + str(deaths_this_year.count()),
                'data': [death['total'] for death in formatted_deaths],
                'backgroundColor': '#6b7280',
                'borderColor': '#6b7280',
                'borderRadius': 50,
            },
            {
                'label': _("marriage certificate").capitalize() + '~' + str(marriages_this_year.count()),
                'data': [marriage['total'] for marriage in formatted_marriages],
                'backgroundColor': "#ff53f6",
                'borderColor': '#ff53f6',
                'borderRadius': 50,
            },
        ]
    }

    context["cetificates_year__data"] = json.dumps(certificates_year)

    births_this_year_fkt = {
        fkt.pk: [births_this_year.filter(
            fokotany=fkt
        ).annotate(gender=models.F('person__gender'))
        .values('gender').annotate(
            count=Count('gender')
        )] for fkt in fokotany
    }
    deaths_this_year_fkt = {
        fkt.pk: [deaths_this_year.filter(
            fokotany=fkt
        ).annotate(gender=models.F('person__gender'))
        .values('gender').annotate(
            count=Count('gender')
        )] for fkt in fokotany
    }
    marriages_this_year_fkt = {
        fkt.pk: [marriages_this_year.filter(
            fokotany=fkt
        ).annotate(gender=models.F('groom__gender'))
        .values('gender').annotate(
            count=Count('gender')
        )] for fkt in fokotany
    }

    # print("Birth", births_this_year_fkt)

    formated_gender = {}

    GENDER_CHOICES = {
            'M': _("Male"),
            'F': _("Female")
        }
    
    for fkt in fokotany:
        formated_gender[fkt.pk] = []
        for gender in GENDER_CHOICES:
            gender_fkt = {
                'gender': GENDER_CHOICES[gender], 
                'count': [0, 0, 0]
            }
            for birth in births_this_year_fkt[fkt.pk][0]:
                if gender == birth['gender']:
                    gender_fkt['count'][0] = int(birth['count'])
            for death in deaths_this_year_fkt[fkt.pk][0]:
                if gender == death['gender']:
                    gender_fkt['count'][1] = int(death['count'])
            for marriage in marriages_this_year_fkt[fkt.pk][0]:
                gender_fkt['count'][2] = int(marriage['count'])

            if gender == 'F':
                gender_fkt['color'] = "#78B7FF"
            else:
                gender_fkt['color'] = "#1F4B7E"
            formated_gender[fkt.pk].append(gender_fkt)

    print(formated_gender)

    certificates_year = {
            fkt.name: json.dumps({
                "labels": [
                     _("birth certificate").capitalize() + '~' + str(births_this_year.filter(fokotany=fkt).count()), 
                    _("death certificate").capitalize() + '~' + str(deaths_this_year.filter(fokotany=fkt).count()),
                    _("marriage certificate").capitalize() + '~' + str(deaths_this_year.filter(fokotany=fkt).count()),
                ],
                "datasets": [
                    {
                        'label': gender['gender'] + f"~{sum(gender['count'])}",
                        'data': gender['count'],
                        'backgroundColor': gender['color'],
                        'borderColor':  gender['color'],
                        'borderRadius': 50,
                    } for gender in formated_gender[fkt.pk]
                ]
            }) for fkt in fokotany
        }
    
    context['cetificates_year_fkt__many'] = {
        fkt.name : sum([
            births_this_year.filter(fokotany=fkt).count(), 
            deaths_this_year.filter(fokotany=fkt).count()
        ]) for fkt in fokotany
    }

    context["cetificates_year_fkt__data"] = certificates_year

    for certificate in BirthCertificate.objects.all():
        context['text'].append(certificate)

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/dashboard.html", context)

@login_required
def birth_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "birth"

    headers = [
            {"name": "status", "header": _("status"), "db_col_name": "person__birthday", "type": "select", "query": ["person__birthday__lte"]},
            {"name": "date", "header": _("date"), "db_col_name": "date_register", "type": "date", "query": ["date_register__date"]},
            {"name": "number", "header": _("number"), "db_col_name": "number", "type": "number", "query": ["number"]},
            {"name": "full name", "header": _("full name"), "db_col_name": "person__last_name" if get_language() == 'mg' else "person__first_name", "type": "search", "query": ["person__last_name__icontains", "person__first_name__icontains"]},
            {"name": "gender", "header": _("gender"), "db_col_name": "person__gender", "type": "select", "query": ["person__gender__icontains"], 'select': GENDER_CHOICES},
            {"name": "age", "header": _("age"), "db_col_name": "person__birthday", "type": "number", "query": ["person__birthday__lte"]},
            {"name": "birthday", "header": _("birthday"), "db_col_name": "person__birthday", "type": "date", "query": ["person__birthday"]},
            {"name": "father", "header": _("father"), "db_col_name": "father__last_name" if get_language() == 'mg' else "father__first_name", "type": "search", "query": ["father__last_name__icontains", "father__first_name__icontains"]},
            {"name": "mother", "header": _("mother"), "db_col_name": "mother__last_name" if get_language() == 'mg' else "mother__first_name", "type": "search", "query": ["mother__last_name__icontains", "mother__first_name__icontains"]},
            {"name": "birth", "header": _("birth"), "db_col_name": "was_alive", "type": "select", "query": ["was_alive"], 'select': {'0': _('alive').capitalize(), '1': _('dead').capitalize()}},
            {"name": "fokotany", "header": _("fokotany"), "db_col_name": "fokotany", "type": "search", "query": ["fokotany__name__icontains"]},
            {"name": "action", "header": _("action"), "db_col_name": "", "type": "", "query": []},
        ]

    add_action_url(__package__, menu_name)
    # print(actions)

    line_bypage = str(request.GET.get('line', 50))

    # Tous les Certificats
    certificates_data = BirthCertificate.objects.all()

    # Recherche
    index_search = int(request.GET.get('search_filter', 3))

    is_searching = False

    if 'q' in request.GET.keys() and request.GET['q'] != "":
        is_searching = True
        print(headers[index_search])
        print(
        date.today() - timedelta(days=int(request.GET['q'])*365) 
                        if headers[index_search]['name'] == 'age'
                        else date(int(request.GET['q'].strip().split('-')[0]), int(request.GET['q'].strip().split('-')[1]), int(request.GET['q'].strip().split('-')[2]))
                        if headers[index_search]['name'] == 'date'
                        else request.GET['q'].strip()
        )

        # print(
        #             Q(**{f"{headers[index_search]['query'][0]}":request.GET['q'].strip()}) |
        #             Q(**{f"{headers[index_search]['query'][1]}":request.GET['q'].strip()})
        #             if len(headers[index_search]['query']) == 2
        #             else
        #             Q(
        #                 **{
        #                     f"{headers[index_search]['query'][0]}": 
        #                     date.today() - timedelta(days=int(request.GET['q'])*365) 
        #                     if headers[index_search]['name'] == 'age'
        #                     else date(int(request.GET['q'].strip().split('-')[0]), int(request.GET['q'].strip().split('-')[1]), int(request.GET['q'].strip().split('-')[2]))
        #                     if headers[index_search]['name'] == 'date' 
        #                     else True if request.GET['q'].strip() == '0' else False
        #                     if headers[index_search]['name'] == 'birth'
        #                     else request.GET['q'].strip()
        #                    }
        #                 )
        #     )

        certificates_data = certificates_data.filter(
                    Q(**{f"{headers[index_search]['query'][0]}":request.GET['q'].strip()}) |
                    Q(**{f"{headers[index_search]['query'][1]}":request.GET['q'].strip()})
                    if len(headers[index_search]['query']) == 2
                    else
                    Q(
                        **{
                            f"{headers[index_search]['query'][0]}": 
                            date.today() - timedelta(days=int(request.GET['q'])*365) 
                            if headers[index_search]['name'] == 'age'
                            else date(int(request.GET['q'].strip().split('-')[0]), int(request.GET['q'].strip().split('-')[1]), int(request.GET['q'].strip().split('-')[2]))
                            if headers[index_search]['name'] == 'date' 
                            else True if request.GET['q'].strip() == '0' else False
                            if headers[index_search]['name'] == 'birth'
                            else request.GET['q'].strip()
                           }
                        )
                )
        # print(certificates_data)

    # Ordre
    ordered = 'order' in list(request.GET) and request.GET['order'].strip() != ''
    order_sense_changeable = False
    order_name = ""
    if ordered:
        # Si la mémoire n'existe pas encore, on la crée
        if not 'order_name' in list(request.session.keys()):
            # print("HEYYYYYYYYYYYYYYYY")
            # Mettre en mémoire le nom de la colonne
            request.session['order_name'] = ""
        if not 'order_asc' in list(request.session.keys()):
            # La première fois, le sens change
            request.session['order_asc'] = True
        # Colonne différente de la précédente
        order_changed = request.GET['order'].strip() != request.session['order_name']
        # Clic sur l'une des colonnes
        order_sense_changeable = request.GET['order'].strip() in [header['name'] + '_touched' for header in headers]
        if order_sense_changeable:
            # print('COLONNE CLIQUEE !!!!!!!!!!!')
            # identification de la colonne
            column = request.GET['order'].strip().replace('_touched', '')
            # Si la colonne est différente de la précedente
            order_changed = column != request.session['order_name']

            # print(column, request.session['order_name'])

            if order_changed:
                # print('Le sens est ascendente')
                request.session['order_name'] = column
                request.session['order_asc'] = True
            else:
                # print('Le sens change')
                # Change de sense
                request.session['order_asc'] = not request.session['order_asc']
            pass
        else:
            # print('Clic sur autre bouton, le sens ne change pas')
            pass

        order_name = request.session['order_name']

        # print(request.session['order_asc'])

        for column in headers:
            if request.session['order_name'] == column['name']:
                # print(column)
                if column['db_col_name'] != "" and not request.session['order_asc']:
                    certificates_data = certificates_data.order_by(column['db_col_name'])
                else:
                    certificates_data = certificates_data.order_by(column['db_col_name']).reverse()
                # print(certificates_data)
                break
    else:
        certificates_data = certificates_data.order_by("date_register").reverse()

    # Pagination
    certificate_bypage = Paginator(certificates_data, line_bypage)

    n_page = int(request.GET.get('num_page', 1))

    if "paging" in list(request.GET.keys()) and n_page in (int(request.GET['paging'].strip()) + 1, int(request.GET['paging'].strip()) - 1) and int(request.GET['paging'].strip()) in certificate_bypage.page_range:
        n_page = int(request.GET['paging'].strip())
        
    # print(n_page)

    certificate_page = certificate_bypage.get_page(n_page)

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
        "is_searching": is_searching,
        "searched_domain": int(request.GET.get('search_filter', 3)),
        "q_value": request.GET.get('q', ""),
        "table_length": line_bypage,
        "order_name": order_name,
        "num_page": certificate_page.number,
        "prev_page": n_page - 1,
        "next_page": n_page + 1,
        "per_page": _(' per ') + str(certificate_bypage.num_pages),
        "table": {
            "headers": headers, 
            "headers_json": json.dumps(headers), 
            "datas": [
                {                                
                    "index" : index,
                    "certificate": birth, 
                    "row": [
                        {"header": "status", "value": (birth.person.birthday.astimezone(TIMEZONE_MGA) + timedelta(days=30)).timestamp() < datetime.now().timestamp(), "style": "", "title": "J" + str((birth.person.birthday.astimezone(TIMEZONE_MGA) + timedelta(days=30)).timetuple().tm_yday - datetime.now().timetuple().tm_yday)},
                        {"header": "date", "value": format(birth.date_register.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": birth.date_register},
                        {"header": "number", "value": "N° " + str(birth.number), "style": "text-center w-12 text-nowrap", "title": "N° " + str(birth.number)},
                        {"header": "full name", "value": birth.person, "style": "text-start w-4 text-nowrap", "title": birth.person},
                        {"header": "gender", "value": Person.GENDER_CHOICES[birth.person.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[birth.person.gender]},
                        {"header": "age", "value": date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year) % {"age": date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year}},
                        {"header": "birthday", "value": birth.person.birthday.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": birth.person.birthday.astimezone(TIMEZONE_MGA)},
                        {"header": "father", "value": birth.father or _("unknown"), "style": "text-start w-4 text-nowrap", "title": birth.father or _("unknown")},
                        {"header": "mother", "value": birth.mother, "style": "text-start w-4 text-nowrap", "title": birth.mother},
                        {"header": "birth", "value": _("alive") if birth.was_alive else _("person"), "style": "text-center w-4 text-nowrap", "title": _("alive") if birth.was_alive else _("person")},
                        {"header": "fokotany", "value": birth.fokotany.name, "style": "text-start w-4 text-nowrap", "title": birth.fokotany},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": "open", "title": _("open"), "url": "civil:person-detail", "style": "blue"},
                            # {"name": "print", "title": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": "delete", "title": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, birth in enumerate(certificate_page)
            ],
        }
    }

    # print("text", context['searched_domain'])

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    # print(context['menu_title'], context['action_name'])

    return render(request, "civil/list.html", context)

@login_required
def birth_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "birth"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    form = CERTIFICATE[menu_name]()

    cert_pk = int(request.POST.get('cert_pk', 0))

    person_pk = int(request.POST.get('person_pk', 0))

    number_initial = "1".zfill(3) if not BirthCertificate.objects.count() else str(BirthCertificate.objects.last().number + 1).zfill(3)

    if person_pk > 0:
        person = Person.objects.get(pk=person_pk)
        # Matricule
        form.fields['fokotany'].initial = person.last_name
        number_initial = str(BirthCertificate.objects.last().number + 1).zfill(3) or '001'
        # form.fields['number'].initial = birth.person.last_name
        # Information personnelle du mort
        form.fields['last_name'].initial = person.last_name
        form.fields['first_name'].initial = person.first_name
        form.fields['gender'].initial = person.gender
        form.fields['birth_place'].initial = person.birth_place
        form.fields['birthday'].initial = person.birthday
        form.fields['is_alive'].initial = person.is_alive

    if cert_pk > 0:
        certificate = BirthCertificate.objects.get(pk=cert_pk)
        # Matricule
        form.fields['fokotany'].initial = certificate.person.last_name
        number_initial = certificate.number
        # form.fields['number'].initial = certificate.person.last_name
        # Information personnelle du mort
        form.fields['last_name'].initial = certificate.person.last_name
        form.fields['first_name'].initial = certificate.person.first_name
        form.fields['gender'].initial = certificate.person.gender
        form.fields['birth_place'].initial = certificate.person.birth_place
        form.fields['birthday'].initial = certificate.person.birthday
        form.fields['is_alive'].initial = certificate.was_alive
        # Information du père
        form.fields['father_exist'].initial = True if certificate.father else False
        if form.fields['father_exist'].initial:
            form.fields['father_last_name'].initial = certificate.father.last_name
            form.fields['father_first_name'].initial = certificate.father.first_name
            form.fields['father_birth_place'].initial = certificate.father.birth_place
            form.fields['father_birthday'].initial = certificate.father.birthday
            form.fields['father_job'].initial = certificate.father.carreer
            form.fields['father_address'].initial = certificate.father.address
        # Information du mère
        form.fields['mother_exist'].initial = True if certificate.mother else False
        form.fields['mother_last_name'].initial = certificate.mother.last_name
        form.fields['mother_first_name'].initial = certificate.mother.first_name
        form.fields['mother_birth_place'].initial = certificate.mother.birth_place
        form.fields['mother_birthday'].initial = certificate.mother.birthday
        form.fields['mother_job'].initial = certificate.mother.carreer
        form.fields['mother_address'].initial = certificate.mother.address
        # Information du mère
        form.fields['declarer_present'].initial = True if certificate.declarer else False
        form.fields['declarer_last_name'].initial = certificate.declarer.last_name
        form.fields['declarer_first_name'].initial = certificate.declarer.first_name
        form.fields['declarer_gender'].initial = certificate.declarer.gender
        form.fields['declarer_birth_place'].initial = certificate.declarer.birth_place
        form.fields['declarer_birthday'].initial = certificate.declarer.birthday
        form.fields['declarer_relation'].initial = certificate.declarer_relationship
        form.fields['declarer_job'].initial = certificate.declarer.carreer
        form.fields['declarer_address'].initial = certificate.declarer.address
        # Information sur l'enregistrement
        form.fields['declaration_date'].initial = certificate.date_declaration
        form.fields['register_date'].initial = certificate.date_register

        print("THAT'S OK")


    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": form,
        "number_initial": number_initial,
        "register_manager": __package__ + ":register_manager",
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "url_save": reverse("civil:birth-save"),
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

    return render(request, "civil/register.html", context)

@login_required
def birth_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    
    menu_name = 'birth'

    print(request.POST.keys())
        
    form = BirthCertificateForm(request.POST)
    print(form.data)

    if form.data:
        # Table Fokotany
        fokotany = Fokotany.objects.get(pk=form.fieldsets_fields[_('Matricule')][0].data)
        # Table Personne
        person, person_created = Person.objects.get_or_create(
            last_name = request.POST['last_name'].strip(),
            first_name = request.POST['first_name'].strip(),
            gender = request.POST['gender'].strip(),
            birthday = None if request.POST['birthday'] == "" else request.POST['birthday'],
            birth_place = request.POST['birth_place'].strip(),
        )
        person.is_alive = True if 'is_alive' in request.POST else False
        person.address = request.POST['mother_address'].strip()
        person.save()

        if "do_certificate" in request.POST:
            print(request.POST['do_certificate'])

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother = Person.objects.get_or_create(
                    last_name = request.POST['mother_last_name'].strip(),
                    first_name = request.POST['mother_first_name'].strip(),
                    gender = 'F',
                    birthday = None if request.POST['mother_birthday'] == "" else request.POST['mother_birthday'],
                    birth_place = request.POST['mother_birth_place'].strip(),
                )[0]
                print(mother)
                mother.carreer = request.POST['mother_job'].strip()
                mother.address = request.POST['mother_address'].strip()
                mother.is_alive = True if 'mother_was_alive' in request.POST else False
                
                if not mother.is_parent:
                    mother.is_parent = True

                mother.save()

            # Si le père existe
            if 'father_exist' in request.POST:
                father = Person.objects.get_or_create(
                    last_name = request.POST['father_last_name'].strip(),
                    first_name = request.POST['father_first_name'].strip(),
                    gender = 'M',
                    birthday = None if request.POST['father_birthday'] == "" else request.POST['father_birthday'],
                    birth_place = request.POST['father_birth_place'].strip(),
                )[0]
                father.carreer = request.POST['father_job'].strip()
                father.address = request.POST['father_address'].strip()
                father.is_alive = True if 'father_was_alive' in request.POST else False

                if father.is_parent:
                    father.is_parent = True

                father.save()
                had_father = True
            else:
                # Sans père
                father = None
                had_father = False

            # déclarant
            declarer = Person.objects.get_or_create(
                last_name = request.POST['declarer_last_name'].strip(),
                first_name = request.POST['declarer_first_name'].strip(),
                gender = request.POST['declarer_gender'].strip(),
                birthday = request.POST['declarer_birthday'],
                birth_place = request.POST['declarer_birth_place'].strip(),
            )[0]
            declarer.address = request.POST['declarer_address'].strip()
            declarer.carreer = request.POST['declarer_job'].strip()
            declarer.save()
            print(declarer)
            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = request.POST['declarer_relation'].strip()
            date_declaration = request.POST['declaration_date']
            date_register = request.POST['register_date']
            responsible_staff = Staff.objects.get(pk=int(request.POST['responsible']))
            number = int(request.POST['number'])

            print(responsible_staff)

            # Table BirthCertificate
            if form.is_valid():
                try:
                    certificate = BirthCertificate.objects.get(person=person)
                    print("BirthCertificate Exists !!!!!!!!!!!!!!!")
                    print(certificate.date_recognization)
                    certificate.father = father
                    if father and not certificate.date_recognization:
                        # Si le père existe et que le certificat n'a jamais été reconnu
                        print("Reconnaissance !!!!!!!!!!!!!!!")
                        certificate.date_recognization = datetime.now()
                        certificate.save()
                        messages.success(request, "BirthCertificate recognized successfully !")
                        ...

                except:
                    BirthCertificate.objects.create(
                        number = number,
                        person = person,
                        father = father,
                        mother = mother,
                        declarer = declarer,
                        declarer_relationship = declarer_relationship,
                        declarer_was_present = declarer_was_present,
                        responsible_staff = responsible_staff,
                        fokotany = fokotany,
                        was_alive = form.cleaned_data.get('is_alive'),
                        had_father = had_father,
                        date_recognization = date_register if 'father_exist' in request.POST else None,
                        date_declaration = date_declaration,
                        date_register = date_register,
                    )
                    messages.success(request, "BirthCertificate created successfully !")
                    
                # certificate_creation(request, menu_name, certificate.pk, many=1)
                return redirect('civil:birth')
            else:
                messages.error(request, "BirthCertificate Creation Error:" + form.errors.as_text())
        else:
            if person_created:
                messages.success(request, "Person created successfully !")
            else:
                messages.error(request, "Person Creation Error !")

        return redirect('civil:birth-register')
    ...

@login_required
def person_detail(request: WSGIRequest, person_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("DETAIL !!!!!!!!!!!!!!!!!!!")

    menu_name = 'person'

    person = Person.objects.get(pk=person_id)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "certificate": {},
        "document": {},
        "document_count": 0,
        "age": 0,
        "status": "",
        "mother_certificated": False,
        "person": person,
    }
    
    birth = BirthCertificate.objects.get(person_id=person_id) if BirthCertificate.objects.filter(person_id=person_id) else None
    death = DeathCertificate.objects.get(person_id=person_id) if DeathCertificate.objects.filter(person_id=person_id) else None
    birth_doc = BirthCertificateDocument.objects.filter(
        certificate=birth, 
        # status="V",
    )
    death_doc = DeathCertificateDocument.objects.filter(
        certificate=death, 
        # status="V",
    )

    # print(death_doc)

    context['birth_doc'] = birth_doc
    context['death_doc'] = death_doc

    document = sorted(
        chain(
            birth_doc, 
            death_doc,
        ),
        key=attrgetter('date_created'),
        reverse=True
    )

    # print(birth.date_declaration)
    context["birth_certificate"] = birth
    context["death_certificate"] = death
    context["age"] = ngettext("%(age)d year old", "%(age)d years old", date.today().year - person.birthday.astimezone(TIMEZONE_MGA).year) % {"age": date.today().year - person.birthday.astimezone(TIMEZONE_MGA).year} if person.birthday else _('unknown')
    context["status"] = _("alive") if person.is_alive else _("dead")

    # Si le père a un certificat de naissance
    if birth:
        context["father_certificated"] = BirthCertificate.objects.get(person=birth.father) if BirthCertificate.objects.filter(person=birth.father) else None
        context["mother_certificated"] = BirthCertificate.objects.get(person=birth.mother) if BirthCertificate.objects.filter(person=birth.mother) else None
        context["declarer_certificated"] = BirthCertificate.objects.get(person=birth.declarer) if BirthCertificate.objects.filter(person=birth.declarer) else None
    else:
        context["father_certificated"] = None
        context["mother_certificated"] = None
        context["declarer_certificated"] = None

    for doc in document:
        context["document_count"] += doc.num_copy 

    context["document"] = document

    if 'cp_birth' in request.POST:
        return redirect('civil:certificate-preview', type_cert=menu_name, pk= birth.pk, many=int(request.POST.get('many_cp', 1)))
    
    
    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/details.html", context)

@login_required
def person_modify(request: WSGIRequest, person_id:int) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    print("MODIFIER LES INFORMATIONS DE LA PERSONNE !!!!!!!!!!!!!!")

    menu_name = "birth"
    
    form = CERTIFICATE['person']()
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    if person_id > 0:
        person = Person.objects.get(pk=person_id)
        # Information personnelle du mort
        form.fields['last_name'].initial = person.last_name
        form.fields['first_name'].initial = person.first_name
        form.fields['gender'].initial = person.gender
        form.fields['birth_place'].initial = person.birth_place
        form.fields['birthday'].initial = person.birthday
        form.fields['job'].initial = person.carreer
        form.fields['address'].initial = person.address
        form.fields['is_alive'].initial = person.is_alive

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": form,
        "register_manager": __package__ + ":register_manager",
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "url_save": reverse("civil:person-save", kwargs={"person_id": person.pk}),
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

    return render(request, 'civil/register.html', context)
    ...

@login_required
def person_save(request: WSGIRequest, person_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    
    print(request.POST.keys())
        
    form = BirthCertificateForm(request.POST)
    print(form.data)

    if form.data:
        person = Person.objects.get(pk=person_id)
        # Table Personne
        person.last_name = request.POST['last_name'].strip()
        person.first_name = request.POST['first_name'].strip()
        person.gender = request.POST['gender'].strip()
        person.birthday = None if request.POST['birthday'] == '' else request.POST['birthday']
        person.birth_place = request.POST['birth_place'].strip()
        person.is_alive = True if 'is_alive' in request.POST else False
        person.carreer = request.POST['job'].strip()
        person.address = request.POST['address'].strip()
        person.save()

    return redirect(person.url_detail)

@login_required
def birth_modify(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("MODIFIE !!!!!!!!!!!!!!!!!!!")
    return redirect('civil:birth')

@login_required
def birth_delete(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    try:
        certificate = BirthCertificate.objects.get(pk=birth_id)
        full_name = certificate.person.full_name
        
        certificate.delete()

        messages.success(request, _('The Certificate of %(name)s deleted successfully.')%{'name': full_name})
    except:
        messages.error(request, _('This certificate cannot be deleted.'))
        ...

    return redirect('civil:birth')

@login_required
def certificate_preview(request: WSGIRequest, pk:int) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    is_doc = False

    print(request.GET)

    type_cert = request.GET.get('type_cert', None)
    many = int(request.GET.get('many_cp', 1))
    notes = ""

    print(request.GET['client_detail'])

    if ('client_detail' in request.GET and request.GET['client_detail'] != '') and ('client_gender' in request.GET and request.GET['client_gender'] != ''):
        notes = GENDER_CLIENT[request.GET['client_gender']] + " " + request.GET['client_detail']

    print(type_cert)

    if '_doc' in type_cert:
        type_cert = type_cert.replace('_doc', "")
        is_doc = True

    menu_name = type_cert

    if is_doc:
        if type_cert == 'birth':
            document = BirthCertificateDocument.objects.get(pk=pk)
            print(document.date_register)
        elif type_cert == 'death':
            document = DeathCertificateDocument.objects.get(pk=pk)
        person = document.certificate.person
    else:
        person = get_object_or_404(Person, pk=pk)
        if type_cert == 'birth':
            birth = get_object_or_404(BirthCertificate, person=person)
            document = BirthCertificateDocument(
                certificate = birth,
                birth_type = birth.birth_type,
                number = birth.number,
                # Person
                person_last_name = birth.person.last_name,
                person_first_name = birth.person.first_name,
                person_gender = birth.person.gender,
                person_birth_place = birth.person.birth_place,
                person_birthday = birth.person.birthday,
                person_address = birth.person.address,
                # Père
                father_last_name = birth.father.last_name if birth.father else None,
                father_first_name = birth.father.first_name if birth.father else None,
                father_birth_place = birth.father.birth_place if birth.father else None,
                father_birthday = birth.father.birthday if birth.father else None,
                father_carreer = birth.father.carreer if birth.father else None,
                father_address = birth.father.address if birth.father else None,
                father_is_alive = birth.father.is_alive if birth.father else False,
                # Mère
                mother_last_name = birth.mother.last_name,
                mother_first_name = birth.mother.first_name,
                mother_birth_place = birth.mother.birth_place,
                mother_birthday = birth.mother.birthday,
                mother_carreer = birth.mother.carreer,
                mother_address = birth.mother.address,
                mother_is_alive = birth.mother.is_alive,
                # Déclarant
                declarer_first_name = birth.declarer.first_name,
                declarer_last_name = birth.declarer.last_name,
                declarer_gender = birth.declarer.gender,
                declarer_birth_place = birth.declarer.birth_place,
                declarer_birthday = birth.declarer.birthday,
                declarer_carreer = birth.declarer.carreer,
                declarer_address = birth.declarer.address,
                declarer_relationship = birth.declarer_relationship,
                declarer_was_present = birth.declarer_was_present,
                # register
                had_father = birth.had_father,
                was_alive = birth.was_alive,
                fokotany = birth.fokotany,
                responsible_staff_name = birth.responsible_staff.full_name,
                responsible_staff_role = birth.responsible_staff.role.title if Role.objects.get(service__grade=1, grade=1) == birth.responsible_staff.role else "mpisolotenan'ny Ben'ny Tanàna",
                date_register = birth.date_register,
                date_recognization = birth.date_recognization,
                status = 'D',
                num_copy = many,
                price = ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
            )

            messages.success(request, _('Birth Document created successfully.'))
            
        elif type_cert == 'death':
            print("DEATH !!!!!!!!!")
            death = DeathCertificate.objects.get(person=person)
            print(death.number)
            document = DeathCertificateDocument(
                certificate = death,
                number = death.number,
                # Person
                person_last_name = death.person.last_name,
                person_first_name = death.person.first_name,
                person_birth_place = death.person.birth_place,
                person_birthday = death.person.birthday,
                person_carreer = death.person.carreer,
                person_address = death.person.address,
                # Père
                father_last_name = death.father.last_name if death.father else "",
                father_first_name = death.father.first_name if death.father else "",
                father_birth_place = death.father.birth_place if death.father else "",
                father_birthday = death.father.birthday if death.father else None,
                father_carreer = death.father.carreer if death.father else "",
                father_address = death.father.address if death.father else "",
                father_is_alive = death.father.is_alive if death.father else False,
                # Mère
                mother_last_name = death.mother.last_name if death.mother else "",
                mother_first_name = death.mother.first_name if death.mother else "",
                mother_birth_place = death.mother.birth_place if death.mother else "",
                mother_birthday = death.mother.birthday if death.mother else None,
                mother_carreer = death.mother.carreer if death.mother else "",
                mother_address = death.mother.address if death.mother else "",
                mother_is_alive = death.mother.is_alive if death.mother else False,
                # Déclarant
                declarer_first_name = death.declarer.first_name,
                declarer_last_name = death.declarer.last_name,
                declarer_birth_place = death.declarer.birth_place,
                declarer_birthday = death.declarer.birthday,
                declarer_carreer = death.declarer.carreer,
                declarer_address = death.declarer.address,
                declarer_relationship = death.declarer_relationship,
                declarer_was_present = death.declarer_was_present,
                # register
                death_day = death.death_day,
                death_place = death.death_place,
                fokotany = death.fokotany,
                responsible_staff_name = death.responsible_staff.full_name,
                responsible_staff_role = death.responsible_staff.role.title,
                date_register = death.date_register,
                date_created = datetime.now(),
                status = 'D',
                num_copy = many,
                price = ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
            )

            messages.success(request, _('Death Document created successfully.'))
            # messages.error(request, _('This death certificate cannot be created.'))

        document.save()

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "document": document,
        "type_cert": type_cert,
        "certificate": document.certificate,
        "many_document": range(document.num_copy),
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/preview.html", context)

@login_required
def certificate_creation(request: WSGIRequest, type_cert:str, pk:int, many:int):
    """Vue pour l'impression (version simplifiée sans boutons)"""
    
    birth = get_object_or_404(BirthCertificate, pk=pk)

    if type_cert == 'birth':
        try:
            document = BirthCertificateDocument(
                certificate = birth,
                father = birth.father,
                father_carreer = birth.father_carreer,
                father_address = birth.father_address,
                mother_carreer = birth.mother_carreer,
                mother_address = birth.mother_address,
                declarer_carreer = birth.declarer_carreer,
                declarer_address = birth.declarer_address,
                was_alive = birth.was_alive,
                date_register = birth.date_register,
                document_number = birth.number,
                status = 'D',
                num_copy = many,
                price = ServicePrice.objects.get(pk=1).certificate_price,
                notes = GENDER_CLIENT[request.POST.get('client_gender', '')] + " " + request.POST['client_detail'] if request.POST.get('client_detail', None) else None,
            )
            document.save()

            messages.success(request, _('Birth Certificate created successfully.'))
            return redirect(__package__+':birth', pk=pk)
        except:
            messages.error(request, _('This birth certificate cannot be created.'))
            return redirect(__package__+':person-detail', pk=document.certificate.pk)
    elif type_cert == 'death':
        print("DEATH !!!!!!!!!")
        try:
            death = get_object_or_404(DeathCertificate, person=birth.person)
            document = DeathCertificateDocument(
                certificate = death,
                status = 'D',
                num_copy = many,
                price = ServicePrice.objects.get(pk=1).certificate_price,
                notes = GENDER_CLIENT[request.POST.get('client_gender', '')] + " " + request.POST['client_detail'] if request.POST.get('client_detail', None) else None,
            )
            document.save()

            messages.success(request, _('Death Certificate created successfully.'))
            return redirect(__package__+':birth', pk=pk)
        except:
            messages.error(request, _('This death certificate cannot be created.'))
            return redirect(__package__+':person-detail', pk=document.certificate.pk)
    else:
        messages.error(request, _('This certificate cannot be created.'))
        if type_cert == 'death':
            return redirect(__package__+':death')
    

    # try:
    #     if menu == 'birth':
    #         document = get_object_or_404(BirthCertificateDocument, pk=pk)
    #         document.status = "V"
    #     elif menu == 'death':
    #         document = get_object_or_404(DeathCertificateDocument, person=pk)
    #         document.status = "V"
    #     document.save()
    #     return JsonResponse({"price": document.get_total_price})
    # except:
    #     return JsonResponse({'error': 'Birth not found'}, status=404)

@login_required
def certificate_validate(request: WSGIRequest, menu:str, pk):
    """Valider un certificat"""

    try:
        if menu == 'birth':
            document = get_object_or_404(BirthCertificateDocument, pk=pk)
            document.date_validated = datetime.now()
            document.validated_by = Staff.objects.get(role__access=request.user) if Staff.objects.filter(role__access=request.user) else None
            document.status = "V"
        elif menu == 'death':
            document = get_object_or_404(DeathCertificateDocument, pk=pk)
            document.date_validated = datetime.now()
            document.validated_by = Staff.objects.get(role__access=request.user) if Staff.objects.filter(role__access=request.user) else None
            document.status = "V"
        document.save()
        return JsonResponse({"price": document.get_total_price})
    except:
        return JsonResponse({'error': 'Birth not found'}, status=404)

@login_required
def certificate_deletion(request: WSGIRequest, menu:str, pk:int):
    """Valider un certificat"""


    if '_doc' in menu:
        menu = menu.replace('_doc', '')

    if menu == "birth":
        document = get_object_or_404(BirthCertificateDocument, pk=pk)
        person = document.certificate.person.pk
    if menu == "death":
        document = get_object_or_404(DeathCertificateDocument, pk=pk)
        person = document.certificate.person.pk
    
    if document.can_delete:
        response = document.delete()
        print(response)
        messages.success(request, _('Certificate deleted successfully.'))
    else:
        messages.error(request, _('This certificate cannot be deleted.'))
    
    if menu == "birth" or (menu == 'death' and BirthCertificate.objects.filter(person_id=person)):
        return redirect(__package__+':person-detail', person)
    if menu == "death":
        return redirect(__package__+':death')

@login_required
def death(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "death"

    headers = [
            {"name": "date", "header": _("date"), "db_col_name": "date_created", "type": "date", "query": ["date_created__date"]},
            {"name": "number", "header": _("number"), "db_col_name": "pk", "type": "number", "query": ["pk"]},
            {"name": "full name", "header": _("full name"), "db_col_name": "person__last_name" if get_language() == 'mg' else "person__first_name", "type": "search", "query": ["person__last_name__icontains", "person__first_name__icontains"]},
            {"name": "gender", "header": _("gender"), "db_col_name": "person__gender", "type": "select", "query": ["person__gender__icontains"], 'select': GENDER_CHOICES},
            {"name": "lived", "header": _("lived"), "db_col_name": "death_day", "type": "number", "query": ["death_day__lte"]},
            {"name": "birthday", "header": _("birthday"), "db_col_name": "person__birthday", "type": "date", "query": ["person__birthday"]},
            {"name": "death day", "header": _("death day"), "db_col_name": "death_day", "type": "date", "query": ["death_day"]},
            {"name": "father", "header": _("father"), "db_col_name": "father_full_name", "type": "search", "query": ["father_full_name__icontains"]},
            {"name": "mother", "header": _("mother"), "db_col_name": "mother_full_name", "type": "search", "query": ["mother_full_name__icontains"]},
            {"name": "fokotany", "header": _("fokotany"), "db_col_name": "fokotany", "type": "search", "query": ["fokotany__name__icontains"]},
            {"name": "action", "header": _("action"), "db_col_name": "", "type": "", "query": []},
        ]

    add_action_url(__package__, menu_name)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    certificates_data = DeathCertificate.objects.all()

    # Recherche
    index_search = int(request.GET.get('search_filter', 2))

    is_searching = False

    if 'q' in request.GET.keys() and request.GET['q'] != "":
        is_searching = True
        print(headers[index_search])
        print(
        date.today() - timedelta(days=int(request.GET['q'])*365) 
                        if headers[index_search]['name'] == 'age' 
                        else date(int(request.GET['q'].strip().split('-')[0]), int(request.GET['q'].strip().split('-')[1]), int(request.GET['q'].strip().split('-')[2]))
                        if headers[index_search]['name'] == 'date'
                        else request.GET['q'].strip()
        )
        certificates_data = certificates_data.filter(
                    Q(**{f"{headers[index_search]['query'][0]}":request.GET['q'].strip()}) |
                    Q(**{f"{headers[index_search]['query'][1]}":request.GET['q'].strip()})
                    if len(headers[index_search]['query']) == 2
                    else
                    Q(
                        **{
                            f"{headers[index_search]['query'][0]}":
                            date.today() - timedelta(days=int(request.GET['q'])*365) 
                            if headers[index_search]['name'] in ['age', 'lived'] 
                            else date(int(request.GET['q'].strip().split('-')[0]), int(request.GET['q'].strip().split('-')[1]), int(request.GET['q'].strip().split('-')[2]))
                            if headers[index_search]['name'] == 'date'
                            else True if request.GET['q'].strip() == '0' else False
                            if headers[index_search]['name'] == 'birth'
                            else request.GET['q'].strip()
                           }
                        )

                )

    # Ordre
    ordered = 'order' in list(request.GET) and request.GET['order'].strip() != ''
    order_sense_changeable = False
    order_name = ""
    if ordered:
        # Si la mémoire n'existe pas encore, on la crée
        if not 'order_name' in list(request.session.keys()):
            print("HEYYYYYYYYYYYYYYYY")
            # Mettre en mémoire le nom de la colonne
            request.session['order_name'] = ""
        if not 'order_asc' in list(request.session.keys()):
            # La première fois, le sens change
            request.session['order_asc'] = True
        # Colonne différente de la précédente
        order_changed = request.GET['order'].strip() != request.session['order_name']
        # Clic sur l'une des colonnes
        order_sense_changeable = request.GET['order'].strip() in [header['name'] + '_touched' for header in headers]
        if order_sense_changeable:
            print('COLONNE CLIQUEE !!!!!!!!!!!')
            # identification de la colonne
            column = request.GET['order'].strip().replace('_touched', '')
            # Si la colonne est différente de la précedente
            order_changed = column != request.session['order_name']

            print(column, request.session['order_name'])

            if order_changed:
                print('Le sens est ascendente')
                request.session['order_name'] = column
                request.session['order_asc'] = True
            else:
                print('Le sens change')
                # Change de sense
                request.session['order_asc'] = not request.session['order_asc']
            pass
        else:
            print('Clic sur autre bouton, le sens ne change pas')
            pass

        order_name = request.session['order_name']

        print(request.session['order_asc'])

        for column in headers:
            if request.session['order_name'] == column['name']:
                print(column)
                if column['db_col_name'] != "" and not request.session['order_asc']:
                    certificates_data = certificates_data.order_by(column['db_col_name'])
                else:
                    certificates_data = certificates_data.order_by(column['db_col_name']).reverse()
                print(certificates_data)
                break
    else:
        certificates_data = certificates_data.order_by("pk").reverse()

    # Pagination
    certificate_bypage = Paginator(certificates_data, line_bypage)

    n_page = int(request.GET.get('num_page', 1))

    if "paging" in list(request.GET.keys()) and n_page in (int(request.GET['paging'].strip()) + 1, int(request.GET['paging'].strip()) - 1) and int(request.GET['paging'].strip()) in certificate_bypage.page_range:
        n_page = int(request.GET['paging'].strip())
        
    print(n_page)

    certificate_page = certificate_bypage.get_page(n_page)

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
        "is_searching": is_searching,
        "searched_domain": int(request.GET.get('search_filter', 2)),
        "q_value": request.GET.get('q', ""),
        "table_length": line_bypage,
        "order_name": order_name,
        "num_page": certificate_page.number,
        "prev_page": n_page - 1,
        "next_page": n_page + 1,
        "per_page": _(' per ') + str(certificate_bypage.num_pages),
        "table": {
            "headers": headers, 
            "headers_json": json.dumps(headers), 
            "datas": []
        }
    }

    for index, death in enumerate(certificate_page):
        if BirthCertificate.objects.filter(person=death.person) and BirthCertificate.objects.filter(person=BirthCertificate.objects.get(person=death.person).father):
            father_cert_pk = BirthCertificate.objects.get(person=BirthCertificate.objects.get(person=death.person).father).pk 
        else:
            father_cert_pk = None

        if BirthCertificate.objects.filter(person=death.person) and BirthCertificate.objects.filter(person=BirthCertificate.objects.get(person=death.person).mother):
            mother_cert_pk = BirthCertificate.objects.get(person=BirthCertificate.objects.get(person=death.person).mother).pk 
        else:
            mother_cert_pk = None

        context["table"]["datas"] += [
            {                                
                "index" : index,
                "certificate": death,
                "row": [
                    {"header": "date", "value": format(death.date_created.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": death.date_created},
                    {"header": "number", "value": "N° " + death.numero, "style": "text-center w-12 text-nowrap", "title": "N° " + death.numero},
                    {"header": "full name", "value": death.person, "style": "text-start w-4 text-nowrap", "title": death.person},
                    {"header": "gender", "value": Person.GENDER_CHOICES[death.person.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[death.person.gender]},
                    {"header": "lived", "value": death.death_day.astimezone(TIMEZONE_MGA).year - death.person.birthday.astimezone(TIMEZONE_MGA).year if death.person.birthday else _('unknown'), "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", death.death_day.astimezone(TIMEZONE_MGA).year - death.person.birthday.astimezone(TIMEZONE_MGA).year) % {"age": death.death_day.astimezone(TIMEZONE_MGA).year - death.person.birthday.astimezone(TIMEZONE_MGA).year} if death.person.birthday else _('unknown')},
                    {"header": "birthday", "value": death.person.birthday.astimezone(TIMEZONE_MGA) if death.person.birthday else _('unknown'), "style": "text-start w-4 text-nowrap", "title": death.person.birthday.astimezone(TIMEZONE_MGA) if death.person.birthday else _('unknown')},
                    {"header": "death day", "value": death.death_day.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": death.death_day.astimezone(TIMEZONE_MGA)},
                    {"header": "father", "value": death.father.full_name if death.father else _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.father.full_name if death.father else _("unknown")},
                    {"header": "mother", "value": death.mother.full_name if death.mother else _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.mother.full_name if death.mother else _("unknown")},
                    {"header": "fokotany", "value": death.fokotany.name, "style": "text-start w-4 text-nowrap", "title": death.fokotany},
                    {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                        {"name": "open", "title": _("open"), "url": "civil:person-detail", "style": "blue"},
                        # {"name": "print", "title": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                        # {"name": "delete", "title": _("delete"), "url": "civil:death-delete", "style": "red"},
                    ]},
                ],
            }
        ]

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    print(context['menu_title'], context['action_name'])

    return render(request, "civil/list.html", context)


@login_required
def death_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "death"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    form = CERTIFICATE[menu_name]()

    cert_pk = int(request.POST.get('cert_pk', 0))

    person_pk = int(request.POST.get('person_pk', 0))

    number_initial = "1".zfill(3) if not DeathCertificate.objects.count() else str(DeathCertificate.objects.last().number + 1).zfill(3)

    if person_pk > 0:
        person = Person.objects.get(pk=person_pk)
        # Matricule
        form.fields['fokotany'].initial = person.last_name
        number_initial = str(BirthCertificate.objects.last().number + 1).zfill(3) or '001'
        # form.fields['number'].initial = birth.person.last_name
        # Information personnelle du mort
        form.fields['last_name'].initial = person.last_name
        form.fields['first_name'].initial = person.first_name
        form.fields['gender'].initial = person.gender
        form.fields['birth_place'].initial = person.birth_place
        form.fields['birthday'].initial = person.birthday
        # Si la personne a déjà un certificat de naissance
        certificate = BirthCertificate.objects.filter(person=person)
        if certificate:
            certificate = certificate.first()
            # Information du père
            form.fields['father_exist'].initial = True if certificate.father else False
            form.fields['father_last_name'].initial = certificate.father.last_name if certificate.father else None
            form.fields['father_first_name'].initial = certificate.father.first_name if certificate.father else None
            form.fields['father_birth_place'].initial = certificate.father.birth_place if certificate.father else None
            form.fields['father_birthday'].initial = certificate.father.birthday if certificate.father else None
            form.fields['father_address'].initial = certificate.father.address if certificate.father else None
            form.fields['father_job'].initial = certificate.father.carreer if certificate.father else None
            form.fields['father_was_alive'].initial = certificate.father.is_alive if certificate.father else False
            # Information du mère
            form.fields['mother_exist'].initial = True if certificate.mother else False
            form.fields['mother_last_name'].initial = certificate.mother.last_name if certificate.mother else None
            form.fields['mother_first_name'].initial = certificate.mother.first_name if certificate.mother else None
            form.fields['mother_birth_place'].initial = certificate.mother.birth_place if certificate.mother else None
            form.fields['mother_birthday'].initial = certificate.mother.birthday if certificate.mother else None
            form.fields['mother_address'].initial = certificate.mother.address if certificate.mother else None
            form.fields['mother_job'].initial = certificate.mother.carreer if certificate.mother else None
            form.fields['mother_was_alive'].initial = certificate.mother.is_alive if certificate.mother else False


    if cert_pk > 0:
        certificate = BirthCertificate.objects.get(pk=cert_pk)
        # Information personnelle du mort
        form.fields['last_name'].initial = certificate.person.last_name
        form.fields['first_name'].initial = certificate.person.first_name
        form.fields['gender'].initial = certificate.person.gender
        form.fields['birth_place'].initial = certificate.person.birth_place
        form.fields['birthday'].initial = certificate.person.birthday
        form.fields['dead_address'].initial = certificate.person.address
        form.fields['dead_job'].initial = certificate.person.carreer
        # Information du père
        form.fields['father_exist'].initial = True if certificate.father else False
        form.fields['father_last_name'].initial = certificate.father.last_name
        form.fields['father_first_name'].initial = certificate.father.first_name
        form.fields['father_birth_place'].initial = certificate.father.birth_place
        form.fields['father_birthday'].initial = certificate.father.birthday
        form.fields['father_address'].initial = certificate.father.address
        form.fields['father_job'].initial = certificate.father.carreer
        form.fields['father_was_alive'].initial = certificate.father.is_alive
        # Information du mère
        form.fields['mother_exist'].initial = True if certificate.mother else False
        form.fields['mother_last_name'].initial = certificate.mother.last_name
        form.fields['mother_first_name'].initial = certificate.mother.first_name
        form.fields['mother_birth_place'].initial = certificate.mother.birth_place
        form.fields['mother_birthday'].initial = certificate.mother.birthday
        form.fields['mother_address'].initial = certificate.mother.address
        form.fields['mother_job'].initial = certificate.mother.carreer
        form.fields['mother_was_alive'].initial = certificate.mother.is_alive
        print("THAT'S OK")

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": form,
        "number_initial": number_initial,
        "register_manager": __package__ + ":register_manager",
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "url_save": reverse("civil:death-save"),
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

    return render(request, "civil/register.html", context)

@login_required
def death_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    
    menu_name = 'death'

    print(request.POST.keys())
        
    form = DeathCertificateForm(request.POST)
    print(form.data)

    if form.data:
        # Table Fokotany
        fokotany = Fokotany.objects.get(pk=form.fieldsets_fields[_('Matricule')][0].data)
        # Table Personne
        print(request.POST['birthday'])
        person, person_created = Person.objects.get_or_create(
                    last_name = request.POST['last_name'].strip(),
                    first_name = request.POST['first_name'].strip(),
                    gender = request.POST['gender'].strip(),
                    birthday = request.POST['birthday'] if request.POST['birthday'] != '' else None,
                    birth_place = request.POST['birth_place'].strip(),
                )
        
        print(person)

        if "do_certificate" in request.POST:
            print(request.POST['do_certificate'])

            # Information complémentaire du décédé
            death_place = request.POST['death_place'].strip()
            death_day = request.POST['death_day']
            person.carreer = request.POST.get('dead_job').strip()
            person.address = request.POST.get('dead_address').strip()
            person.save()

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother = Person.objects.get_or_create(
                    last_name = request.POST['mother_last_name'].strip(),
                    first_name = request.POST['mother_first_name'].strip(),
                    gender = 'F',
                    birthday =  request.POST['mother_birthday'] if request.POST['mother_birthday'] != '' else None,
                    birth_place = request.POST['mother_birth_place'].strip(),
                )[0]
                print(mother)
                mother.is_alive = True if "father_was_alive" in request.POST else False
                mother.carreer = request.POST['mother_job'].strip()
                mother.address = request.POST['mother_address'].strip()
                mother.save()
            else:
                # Sans père
                mother = None

            # Si le père existe
            if 'father_exist' in request.POST:
                father = Person.objects.get_or_create(
                    last_name = request.POST['father_last_name'].strip(),
                    first_name = request.POST['father_first_name'].strip(),
                    gender = 'M',
                    birthday =  request.POST['father_birthday'] if request.POST['father_birthday'] != '' else None,
                    birth_place = request.POST['father_birth_place'].strip(),
                )[0]
                father.is_alive = True if "mother_was_alive" in request.POST else False
                father.carreer = request.POST['father_job'].strip()
                father.address = request.POST['father_address'].strip()
                father.save()
            else:
                # Sans père
                father = None

            # déclarant
            declarer = Person.objects.get_or_create(
                last_name = request.POST['declarer_last_name'].strip(),
                first_name = request.POST['declarer_first_name'].strip(),
                gender = request.POST['declarer_gender'].strip(),
                birthday = request.POST['declarer_birthday'],
                birth_place = request.POST['declarer_birth_place'].strip(),
            )[0]
            declarer.carreer = request.POST['declarer_job'].strip()
            declarer.address = request.POST['declarer_address'].strip()
            declarer.save()

            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = request.POST['declarer_relation'].strip()
            date_declaration = request.POST['declaration_date']
            date_register = request.POST['register_date']
            number = int(request.POST['number'])

            # Table BirthCertificate
            if form.is_valid():
                try:
                    DeathCertificate.objects.create(
                        number = number,
                        person = person,
                        father = father,
                        mother = mother,
                        declarer = declarer,
                        declarer_relationship = declarer_relationship,
                        declarer_was_present = declarer_was_present,
                        responsible_staff = Staff.objects.get(role=1),
                        fokotany = fokotany,
                        death_day = death_day,
                        death_place = death_place,
                        date_declaration = date_declaration,
                        date_register = date_register,
                    )
        
                    if person.is_alive:
                        person.is_alive = False
                        person.save(update_fields=["is_alive"])

                    return redirect('civil:death')
                except:
                    messages.error(request, "BirthCertificate Creation Error !")
        else:
            if person_created:
                messages.success(request, "Person created successfully !")
            else:
                messages.error(request, "Person Creation Error !")

        return redirect('civil:death-register')
    ...

@login_required
def marriage(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    add_action_url(__package__, menu_name)

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

    return render(request, "civil/list.html", context)

@login_required
def marriage_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    add_action_url(__package__, menu_name)

    form = CERTIFICATE[menu_name]()

    # print(form.fieldsets_fields)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": form,
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

    return render(request, "civil/register.html", context)

@login_required
def register_manager(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    print(request.POST)

    form = BirthCertificateForm(request.POST)
    menu_app = request.session['menu_app']

    print(menu_app, form.is_valid(), form.errors)

    if form.is_valid():
        for field, value in form.cleaned_data.items():
            print(field, ":", value)
        request.session['menu_app'] = None

    return redirect(f"civil:{menu_app}-register")
    ...