from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from itertools import chain
import json
from operator import attrgetter
from django.contrib import messages
from django.urls import reverse_lazy
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

from civil.forms import BirthCertificateForm, DeathCertificateForm, MarriageCertificateForm
from civil.models import BirthCertificate, BirthCertificateDocument, DeathCertificate, DeathCertificateDocument, MarriageCertificate, Person
from civil.templatetags.isa_gasy import VolanaGasy
from finances.models import ServicePrice


CERTIFICATE = {
    "birth": BirthCertificateForm,
    "death": DeathCertificateForm,
    "marriage": MarriageCertificateForm,
}

GENDER_CHOICES = {
    'M': _("Male"),
    'F': _("Female")
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
        return _("%(last_name)s %(first_name)s - born at %(birthday_day)s at %(birthday_hour)s.") % {
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
def search_persons(request, type:str, q_name:str):
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
                data['person_name'][person.pk] = person.full_name + ' born at ' + person.birthday.astimezone(TIMEZONE_MGA).__format__('%d-%m-%Y %H:%M') 
            except OSError:
                data['person_name'][person.pk] = person.full_name + ' born at ' + (person.birthday + timedelta(hours=3)).__format__('%d-%m-%Y %H:%M') 
        
        return JsonResponse(data)
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    ...

@login_required 
def get_person_details(request, person_id):
    """Retourne les détails d'une personne en JSON"""
    try:
        person = Person.objects.get(id=person_id)
        
        data = {
            'fields': [
                person.last_name,
                person.first_name,
                person.gender,
                person.birth_place,
            ]
        }

        data = {
            "last_name": person.last_name,
            "first_name": person.first_name,
            "gender": person.gender,
            "birth_place": person.birth_place,
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

    years_qr = BirthCertificate.objects.annotate(year=TruncYear('born__birthday', tzinfo=TIMEZONE_UTC)).values_list('year').order_by('year').reverse()

    years = [datetime.now().year]

    for year in years_qr:
        if not year[0].year in years:
            years.append(year[0].year)

    # years.reverse()

    births_this_year = births.filter(
        born__birthday__gte=year__first_day,
        born__birthday__lte=year__last_day,
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
        month=TruncMonth('born__birthday', tzinfo=TIMEZONE_UTC)
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
        ).annotate(gender=models.F('born__gender'))
        .values('gender').annotate(
            count=Count('gender')
        )] for fkt in fokotany
    }
    deaths_this_year_fkt = {
        fkt.pk: [deaths_this_year.filter(
            fokotany=fkt
        ).annotate(gender=models.F('dead__gender'))
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

    # actions.insert(
    #     1,
    #     {
    #         'name': "waitting",
    #         'title': "",
    #         'url': ""
    #     }
    # )

    # print(actions)

    headers = [
            {"name": "status", "header": _("status"), "db_col_name": "born__birthday", "type": "select", "query": ["born__birthday__lte"]},
            {"name": "date", "header": _("date"), "db_col_name": "date_register", "type": "date", "query": ["date_register__date"]},
            {"name": "number", "header": _("number"), "db_col_name": "number", "type": "number", "query": ["number"]},
            {"name": "full name", "header": _("full name"), "db_col_name": "born__last_name" if get_language() == 'mg' else "born__first_name", "type": "search", "query": ["born__last_name__icontains", "born__first_name__icontains"]},
            {"name": "gender", "header": _("gender"), "db_col_name": "born__gender", "type": "select", "query": ["born__gender__icontains"], 'select': GENDER_CHOICES},
            {"name": "age", "header": _("age"), "db_col_name": "born__birthday", "type": "number", "query": ["born__birthday__lte"]},
            {"name": "birthday", "header": _("birthday"), "db_col_name": "born__birthday", "type": "date", "query": ["born__birthday"]},
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

    if 'q' in request.GET.keys() and request.GET['q'] != "":
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
                    "pk": birth.pk,
                    "is_alive": birth.born.is_alive,
                    "father_cert_pk": BirthCertificate.objects.get(born=birth.father).pk if BirthCertificate.objects.filter(born=birth.father) else None,
                    "mother_cert_pk": BirthCertificate.objects.get(born=birth.mother).pk if BirthCertificate.objects.filter(born=birth.mother) else None,
                    "detail_url": 'civil:birth-detail',
                    "row": [
                        {"header": "status", "value": (birth.born.birthday.astimezone(TIMEZONE_MGA) + timedelta(days=30)).timestamp() < datetime.now().timestamp(), "style": "", "title": "J" + str((birth.born.birthday.astimezone(TIMEZONE_MGA) + timedelta(days=30)).timetuple().tm_yday - datetime.now().timetuple().tm_yday)},
                        {"header": "date", "value": format(birth.date_register.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": birth.date_register},
                        {"header": "number", "value": "N° " + str(birth.number), "style": "text-center w-12 text-nowrap", "title": "N° " + str(birth.number)},
                        {"header": "full name", "value": birth.born, "style": "text-start w-4 text-nowrap", "title": birth.born},
                        {"header": "gender", "value": Person.GENDER_CHOICES[birth.born.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[birth.born.gender]},
                        {"header": "age", "value": date.today().year - birth.born.birthday.astimezone(TIMEZONE_MGA).year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - birth.born.birthday.astimezone(TIMEZONE_MGA).year) % {"age": date.today().year - birth.born.birthday.astimezone(TIMEZONE_MGA).year}},
                        {"header": "birthday", "value": birth.born.birthday.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": birth.born.birthday.astimezone(TIMEZONE_MGA)},
                        {"header": "father", "value": birth.father or _("unknown"), "style": "text-start w-4 text-nowrap", "title": birth.father or _("unknown")},
                        {"header": "mother", "value": birth.mother, "style": "text-start w-4 text-nowrap", "title": birth.mother},
                        {"header": "birth", "value": _("alive") if birth.was_alive else _("dead"), "style": "text-center w-4 text-nowrap", "title": _("alive") if birth.was_alive else _("dead")},
                        {"header": "fokotany", "value": birth.fokotany.name, "style": "text-start w-4 text-nowrap", "title": birth.fokotany},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("open"), "url": "civil:birth-detail", "style": "blue"},
                            # {"name": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": _("delete"), "url": "civil:birth-delete", "style": "red"},
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

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": CERTIFICATE[menu_name](),
        "number_initial": "1".zfill(3) if not BirthCertificate.objects.count() else str(BirthCertificate.objects.last().number + 1).zfill(3),
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
        born, born_created = Person.objects.get_or_create(
                    last_name = request.POST['last_name'].strip(),
                    first_name = request.POST['first_name'].strip(),
                    gender = request.POST['gender'].strip(),
                    birthday = request.POST['birthday'],
                    birth_place = request.POST['birth_place'].strip(),
                    is_alive = True if 'is_alive' in request.POST else False,
                )

        if "do_certificate" in request.POST:
            print(request.POST['do_certificate'])

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother = Person.objects.get_or_create(
                    last_name = request.POST['mother_last_name'].strip(),
                    first_name = request.POST['mother_first_name'].strip(),
                    gender = 'F',
                    birthday = request.POST['mother_birthday'],
                    birth_place = request.POST['mother_birth_place'].strip(),
                )[0]
                print(mother)
                mother_carreer = request.POST['mother_job'].strip()
                mother_address = request.POST['mother_address'].strip()
                if not mother.is_parent:
                    mother.is_parent = True
                    mother.save(update_fields=["is_parent"])

            # Si le père existe
            if 'father_exist' in request.POST:
                father = Person.objects.get_or_create(
                    last_name = request.POST['father_last_name'].strip(),
                    first_name = request.POST['father_first_name'].strip(),
                    gender = 'M',
                    birthday = request.POST['father_birthday'],
                    birth_place = request.POST['father_birth_place'].strip(),
                )[0]
                father_carreer = request.POST['father_job'].strip()
                father_address = request.POST['father_address'].strip()
                # Sans mariage, Type Birth and Recognization : Fahaterahana sy Fananjahana
                certificate_type = list(BirthCertificate.CERTIFICATE_TYPES.keys())[1]

                if father.is_parent:
                    father.is_parent = True
                    father.save(update_fields=["is_parent"])
            else:
                # Sans père
                father = None
                father_carreer = None
                father_address = None
                # Type Birth : Fahaterahana
                certificate_type = list(BirthCertificate.CERTIFICATE_TYPES.keys())[0]

                if MarriageCertificate.objects.filter(groom=father, bride=mother, is_active=True).exists():
                    # Les parents sont actuellement mariés, Type Birth : Fahaterahana
                    certificate_type = list(BirthCertificate.CERTIFICATE_TYPES.keys())[0]

            # déclarant
            declarer = Person.objects.get_or_create(
                last_name = request.POST['declarer_last_name'].strip(),
                first_name = request.POST['declarer_first_name'].strip(),
                gender = request.POST['declarer_gender'].strip(),
                birthday = request.POST['declarer_birthday'],
                birth_place = request.POST['declarer_birth_place'].strip(),
            )[0]
            print(declarer)
            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = request.POST['declarer_relation'].strip()
            declarer_carreer = request.POST['declarer_job'].strip()
            declarer_address = request.POST['declarer_address'].strip()
            date_declaration = request.POST['declaration_date']
            date_register = request.POST['register_date']
            number = int(request.POST['number'])

            # Table BirthCertificate
            if form.is_valid():
                BirthCertificate.objects.create(
                    number = number,
                    born = born,
                    father = father,
                    father_carreer = father_carreer,
                    father_address = father_address,
                    mother = mother,
                    mother_carreer = mother_carreer,
                    mother_address = mother_address,
                    declarer = declarer,
                    declarer_relationship = declarer_relationship,
                    declarer_carreer = declarer_carreer,
                    declarer_address = declarer_address,
                    declarer_was_present = declarer_was_present,
                    responsible_staff = Staff.objects.get(role=1),
                    fokotany = fokotany,
                    certificate_type = certificate_type,
                    was_alive = form.cleaned_data.get('is_alive'),
                    date_declaration = date_declaration,
                    date_register = date_register,
                )
                
                # certificate_creation(request, menu_name, certificate.pk, many=1)

                return redirect('civil:birth')
            else:
                messages.error(request, "BirthCertificate Creation Error:" + form.errors.as_text)
        else:
            if born_created:
                messages.success(request, "Person created successfully !")
            else:
                messages.error(request, "Person Creation Error !")

        return redirect('civil:birth-register')
    ...

@login_required
def birth_detail(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("DETAIL !!!!!!!!!!!!!!!!!!!")

    menu_name = 'birth'

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
    }
    certificate = BirthCertificate.objects.get(pk=birth_id)
    birth_doc = BirthCertificateDocument.objects.filter(certificate=certificate)
    death_doc = DeathCertificateDocument.objects.filter(certificate__dead=certificate.born)

    print(birth_doc)

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

    print(certificate.date_declaration)
    context["certificate"] = certificate
    context["age"] = ngettext("%(age)d year old", "%(age)d years old", date.today().year - certificate.born.birthday.astimezone(TIMEZONE_MGA).year) % {"age": date.today().year - certificate.born.birthday.astimezone(TIMEZONE_MGA).year}
    context["status"] = _("alive") if certificate.born.is_alive else _("dead")

    # Si le père a un certificat de naissance
    context["father_certificated"] = BirthCertificate.objects.get(born=certificate.father) if BirthCertificate.objects.filter(born=certificate.father) else None
    context["mother_certificated"] = BirthCertificate.objects.get(born=certificate.mother) if BirthCertificate.objects.filter(born=certificate.mother) else None
    context["declarer_certificated"] = BirthCertificate.objects.get(born=certificate.declarer) if BirthCertificate.objects.filter(born=certificate.declarer) else None

    for doc in document:
        context["document_count"] += doc.num_copy 

    try:
        print(document[0].certificate.pk)
        context["document"] = document
    except IndexError:
        ...

    if 'cp_birth' in request.POST:
        return redirect('civil:certificate-preview', type_cert=menu_name, pk= certificate.pk, many=int(request.POST.get('many_cp', 1)))
    
    
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
def birth_modify(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("MODIFIE !!!!!!!!!!!!!!!!!!!")
    return redirect('civil:birth')

@login_required
def birth_delete(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    print(BirthCertificate.objects.get(pk=birth_id).delete())
    print("SUPPRIME !!!!!!!!!!!!!!!!!!!")
    return redirect('civil:birth')

@login_required
def certificate_preview(request: WSGIRequest, pk:int, type_cert='birth', many=1) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    is_doc = False

    if '_doc' in type_cert:
        type_cert = type_cert.replace('_doc', "")
        is_doc = True

    menu_name = type_cert

    if is_doc:
        if type_cert == 'birth':
            document = get_object_or_404(BirthCertificateDocument, pk=pk)
    else:
        if type_cert == 'birth':
            birth = get_object_or_404(BirthCertificate, pk=pk)
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
                date_created = datetime.now(),
                price = ServicePrice.objects.get(pk=1).certificate_price,
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
        "document": document,
        "type_cert": type_cert,
        "many": many,
        "many_document": range(many),
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
def certificate_creation(request, menu:str, pk:int, many=1):
    """Vue pour l'impression (version simplifiée sans boutons)"""

    try:
        if menu == 'birth':
            certificate = get_object_or_404(BirthCertificate, pk=pk)
            print(certificate)
            document = BirthCertificateDocument(
                certificate=certificate,
                father=certificate.father,
                father_carreer=certificate.father_carreer,
                father_address=certificate.father_address,
                mother_carreer=certificate.mother_carreer,
                mother_address=certificate.mother_address,
                declarer_carreer=certificate.declarer_carreer,
                declarer_address=certificate.declarer_address,
                was_alive=certificate.was_alive,
                document_number=certificate.number,
                status="V",
                price=ServicePrice.objects.last().certificate_price,
                num_copy=many,
                date_register=certificate.date_register
            )
        elif menu == 'death':
            certificate = get_object_or_404(DeathCertificate, dead=pk)
            print(certificate)
            document = DeathCertificateDocument(
                certificate=certificate,
                document_number=certificate.number,
                status="V",
                price=ServicePrice.objects.last().certificate_price,
                num_copy=many,
                date_register=certificate.date_register
            )
        document.save()
        return JsonResponse({"price": document.get_total_price})
    except:
        return JsonResponse({'error': 'Birth not found'}, status=404)

def certificate_validate(request, pk):
    """Valider un certificat"""
    document = get_object_or_404(BirthCertificateDocument, pk=pk)
    
    if document.can_edit:
        document.status = 'VALIDATED'
        document.validated_by = request.user.get_full_name() or request.user.username
        document.validated_at = timezone.now()
        document.save()
        messages.success(request, _('Certificate validated successfully.'))
    else:
        messages.error(request, _('This certificate cannot be validated.'))
    
    return redirect('certificate-preview', pk=pk)


class CertificateDeleteView(DeleteView):
    """Vue pour supprimer un certificat"""
    model = BirthCertificateDocument
    success_url = reverse_lazy('certificate-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if not self.object.can_delete:
            messages.error(request, _('This certificate cannot be deleted.'))
            return redirect('certificate-preview', pk=self.object.pk)
        
        messages.success(request, _('Certificate deleted successfully.'))
        return super().delete(request, *args, **kwargs)

@login_required
def death(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "death"

    headers = [
            {"name": "date", "header": _("date"), "db_col_name": "date_created", "type": "date", "query": ["date_created__date"]},
            {"name": "number", "header": _("number"), "db_col_name": "pk", "type": "number", "query": ["pk"]},
            {"name": "full name", "header": _("full name"), "db_col_name": "dead__last_name" if get_language() == 'mg' else "dead__first_name", "type": "search", "query": ["dead__last_name__icontains", "dead__first_name__icontains"]},
            {"name": "gender", "header": _("gender"), "db_col_name": "dead__gender", "type": "select", "query": ["dead__gender__icontains"], 'select': Person.GENDER_CHOICES},
            {"name": "lived", "header": _("lived"), "db_col_name": "death_day", "type": "number", "query": ["death_day__lte"]},
            {"name": "birthday", "header": _("birthday"), "db_col_name": "dead__birthday", "type": "date", "query": ["dead__birthday"]},
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

    if 'q' in request.GET.keys() and request.GET['q'] != "":
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
            "datas": []
        }
    }

    for index, death in enumerate(certificate_page):
        if BirthCertificate.objects.filter(born=death.dead) and BirthCertificate.objects.filter(born=BirthCertificate.objects.get(born=death.dead).father):
            father_cert_pk = BirthCertificate.objects.get(born=BirthCertificate.objects.get(born=death.dead).father).pk 
        else:
            father_cert_pk = None

        if BirthCertificate.objects.filter(born=death.dead) and BirthCertificate.objects.filter(born=BirthCertificate.objects.get(born=death.dead).mother):
            mother_cert_pk = BirthCertificate.objects.get(born=BirthCertificate.objects.get(born=death.dead).mother).pk 
        else:
            mother_cert_pk = None

        context["table"]["datas"] += [
            {                                
                "index" : index,
                "pk": BirthCertificate.objects.get(born=death.dead).pk if BirthCertificate.objects.filter(born=death.dead) else None,
                "father_cert_pk": father_cert_pk,
                "mother_cert_pk": mother_cert_pk,
                "detail_url": 'civil:birth-detail',
                "row": [
                    {"header": "date", "value": format(death.date_created.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": death.date_created},
                    {"header": "number", "value": "N° " + death.numero, "style": "text-center w-12 text-nowrap", "title": "N° " + death.numero},
                    {"header": "full name", "value": death.dead, "style": "text-start w-4 text-nowrap", "title": death.dead},
                    {"header": "gender", "value": Person.GENDER_CHOICES[death.dead.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[death.dead.gender]},
                    {"header": "lived", "value": death.death_day.astimezone(TIMEZONE_MGA).year - death.dead.birthday.astimezone(TIMEZONE_MGA).year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", death.death_day.astimezone(TIMEZONE_MGA).year - death.dead.birthday.astimezone(TIMEZONE_MGA).year) % {"age": death.death_day.astimezone(TIMEZONE_MGA).year - death.dead.birthday.astimezone(TIMEZONE_MGA).year}},
                    {"header": "birthday", "value": death.dead.birthday.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": death.dead.birthday.astimezone(TIMEZONE_MGA)},
                    {"header": "death day", "value": death.death_day.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": death.death_day.astimezone(TIMEZONE_MGA)},
                    {"header": "father", "value": death.father_full_name or _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.father_full_name or _("unknown")},
                    {"header": "mother", "value": death.mother_full_name or _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.mother_full_name or _("unknown")},
                    {"header": "fokotany", "value": death.fokotany.name, "style": "text-start w-4 text-nowrap", "title": death.fokotany},
                    {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                        {"name": _("open"), "url": "civil:birth-detail", "style": "blue"},
                        # {"name": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                        # {"name": _("delete"), "url": "civil:death-delete", "style": "red"},
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

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": CERTIFICATE[menu_name](),
        "number_initial": "1".zfill(3) if not DeathCertificate.objects.count() else str(BirthCertificate.objects.last().number + 1).zfill(3),
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
        dead, dead_created = Person.objects.get_or_create(
                    last_name = request.POST['last_name'].strip(),
                    first_name = request.POST['first_name'].strip(),
                    gender = request.POST['gender'].strip(),
                    birthday = request.POST['birthday'],
                    birth_place = request.POST['birth_place'].strip(),
                )
        
        print(dead)
        
        if dead.is_alive:
            dead.is_alive = False
            dead.save(update_fields=["is_alive"])

        if "do_certificate" in request.POST:
            print(request.POST['do_certificate'])

            # Information complémentaire du décédé
            death_place = request.POST['death_place'].strip()
            death_day = request.POST['death_day']
            dead_carreer = request.POST.get('dead_job').strip()
            dead_address = request.POST.get('dead_address').strip()
            
            dead_is_older = date.today().year - Person.objects.get(pk=dead.pk).birthday.year >= 50

            if dead_is_older:
                father_is_alive = False
                mother_is_alive = False
            else:
                father_is_alive = True
                mother_is_alive = True

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother_full_name = request.POST['mother_last_name'].strip() + " " + request.POST['mother_first_name'].strip()
                print(mother_full_name)
                mother_is_alive = True if 'mother_was_alive' in request.POST else False
            else:
                # Sans mère
                mother_full_name = None
            
            # Si le père existe
            if 'father_exist' in request.POST:
                father_full_name = request.POST['father_last_name'].strip() + " " + request.POST['father_first_name'].strip()
                print(father_full_name)
                father_is_alive = True if 'father_was_alive' in request.POST else False
            else:
                # Sans père
                father_full_name = None

            # déclarant
            declarer = Person.objects.get_or_create(
                last_name = request.POST['declarer_last_name'].strip(),
                first_name = request.POST['declarer_first_name'].strip(),
                gender = request.POST['declarer_gender'].strip(),
                birthday = request.POST['declarer_birthday'],
                birth_place = request.POST['declarer_birth_place'].strip(),
            )[0]
            print(declarer)
            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = request.POST['declarer_relation'].strip()
            declarer_carreer = request.POST['declarer_job'].strip()
            declarer_address = request.POST['declarer_address'].strip()
            date_declaration = request.POST['declaration_date']
            number = int(request.POST['number'])

            # Table BirthCertificate
            if form.is_valid():
                DeathCertificate.objects.create(
                    number = number,
                    dead = dead,
                    death_day = death_day,
                    death_place = death_place,
                    dead_carreer = dead_carreer,
                    dead_address = dead_address,
                    father_full_name = father_full_name,
                    father_is_alive = father_is_alive,
                    mother_full_name = mother_full_name,
                    mother_is_alive = mother_is_alive,
                    declarer = declarer,
                    declarer_relationship = declarer_relationship,
                    declarer_was_present = declarer_was_present,
                    declarer_carreer = declarer_carreer,
                    declarer_address = declarer_address,
                    responsible_staff = Staff.objects.get(role=1),
                    fokotany = fokotany,
                    date_declaration = date_declaration,
                )

                return redirect('civil:death')
            else:
                messages.error(request, "BirthCertificate Creation Error:" + form.errors.as_text)
        else:
            if dead_created:
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

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": MarriageCertificateForm(),
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