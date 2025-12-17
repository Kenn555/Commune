from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from itertools import chain
import json
from operator import attrgetter
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, DeleteView
from django.db import IntegrityError, models
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
from babel.dates import format_date

from civil.forms import BirthCertificateForm, DeathCertificateForm, MarriageCertificateForm, PersonForm
from civil.models import BirthCertificate, BirthCertificateDocument, DeathCertificate, DeathCertificateDocument, MarriageCertificate, MarriageCertificateDocument, Person, RecognizationCertificate, RecognizationCertificateDocument
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
            "pk": person.pk,
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

    print(request.session['urls'])

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
        "birth_count": births.count(),
        "death_count": deaths.count(),
        "marriage_count": marriages.count(),
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
        "responsible_staffs": Staff.objects.filter(role__service__grade=1).order_by('role__grade'),
        "mother_certificated": False,
        "person": person,
    }
    
    birth = BirthCertificate.objects.get(person_id=person_id) if BirthCertificate.objects.filter(person_id=person_id) else None
    recognization = RecognizationCertificate.objects.get(person=person_id) if RecognizationCertificate.objects.filter(person=person_id) else None
    if person.gender == "M":
        if MarriageCertificate.objects.filter(groom=person_id, is_active=True):
            marriage = MarriageCertificate.objects.get(groom=person_id) 
        else:
            marriage = None
    else:
        if MarriageCertificate.objects.filter(bride=person_id, is_active=True):
            marriage = MarriageCertificate.objects.get(bride=person_id) 
        else:
            marriage = None
    death = DeathCertificate.objects.get(person_id=person_id) if DeathCertificate.objects.filter(person_id=person_id) else None

    birth_doc = BirthCertificateDocument.objects.filter(
        certificate=birth, 
        # status="V",
    )
    recognization_doc = RecognizationCertificateDocument.objects.filter(
        certificate=recognization, 
        # status="V",
    )
    marriage_doc = MarriageCertificateDocument.objects.filter(
        certificate=marriage, 
        # status="V",
    )
    death_doc = DeathCertificateDocument.objects.filter(
        certificate=death, 
        # status="V",
    )

    # print(death_doc)

    context['birth_doc'] = birth_doc
    context['recognization_doc'] = recognization_doc
    context['marriage_doc'] = marriage_doc
    context['death_doc'] = death_doc

    document = sorted(
        chain(
            birth_doc, 
            recognization_doc,
            marriage_doc,
            death_doc,
        ),
        key=attrgetter('date_created'),
        reverse=True
    )

    # print(birth.date_declaration)
    context["birth_certificate"] = birth
    context["recognization_certificate"] = recognization
    context["marriage_certificate"] = marriage
    context["death_certificate"] = death

    if death:
        context["age"] = ngettext("%(age)d year old", "%(age)d years old", death.death_day.year - person.birthday.astimezone(TIMEZONE_MGA).year) % {"age": death.death_day.year - person.birthday.astimezone(TIMEZONE_MGA).year} if person.birthday else _('unknown')
    else:
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
        form.fields['birthday'].initial = person.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")
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
        person.last_name = form.data['last_name']
        person.first_name = form.data['first_name']
        person.gender = form.data['gender']
        person.birthday = None if form.data['birthday'] == '' else form.data['birthday']
        person.birth_place = form.data['birth_place']
        person.is_alive = True if 'is_alive' in request.POST else False
        person.carreer = form.data['job']
        person.address = form.data['address']

        try:
            person.save()
            messages.success(request, _('Person Modificated Successfully !'))
        except:
            messages.error(request, _('Person Modification Error !'))

    return redirect(person.url_detail)


@login_required
def person_delete(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    try:
        person = Person.objects.get(pk=birth_id)
        
        person.delete()

        messages.success(request, _('The Certificate of %(name)s deleted successfully.')%{'name': person.full_name})
    except:
        messages.error(request, _('This certificate cannot be deleted.'))
        ...

    return redirect('civil:birth')

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
                        else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                        if headers[index_search]['name'] == 'date'
                        else request.GET['q']
        )

        certificates_data = certificates_data.filter(
                    Q(**{f"{headers[index_search]['query'][0]}":request.GET['q']}) |
                    Q(**{f"{headers[index_search]['query'][1]}":request.GET['q']})
                    if len(headers[index_search]['query']) == 2
                    else
                    Q(
                        **{
                            f"{headers[index_search]['query'][0]}": 
                            date.today() - timedelta(days=int(request.GET['q'])*365) 
                            if headers[index_search]['name'] == 'age'
                            else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                            if headers[index_search]['name'] == 'date' 
                            else True if request.GET['q'] == '0' else False
                            if headers[index_search]['name'] == 'birth'
                            else request.GET['q']
                           }
                        )
                )

    # Ordre
    ordered = 'order' in list(request.GET) and request.GET['order'] != ''
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
        order_changed = request.GET['order'] != request.session['order_name']
        # Clic sur l'une des colonnes
        order_sense_changeable = request.GET['order'] in [header['name'] + '_touched' for header in headers]
        if order_sense_changeable:
            # print('COLONNE CLIQUEE !!!!!!!!!!!')
            # identification de la colonne
            column = request.GET['order'].replace('_touched', '')
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

    if "paging" in list(request.GET.keys()) and n_page in (int(request.GET['paging']) + 1, int(request.GET['paging']) - 1) and int(request.GET['paging']) in certificate_bypage.page_range:
        n_page = int(request.GET['paging'])
        
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
                        {"header": "status", "value": "full", "style": "", "title": "J" + str((birth.person.birthday.astimezone(TIMEZONE_MGA) + timedelta(days=30)).timetuple().tm_yday - datetime.now().timetuple().tm_yday)},
                        {"header": "date", "value": format(birth.date_register.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": birth.date_register},
                        {"header": "number", "value": "N° " + str(birth.number), "style": "text-center w-12 text-nowrap", "title": "N° " + str(birth.number)},
                        {"header": "full name", "value": birth.person, "style": "text-start w-4 text-nowrap", "title": birth.person},
                        {"header": "gender", "value": Person.GENDER_CHOICES[birth.person.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[birth.person.gender]},
                        {"header": "age", "value": date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year) % {"age": date.today().year - birth.person.birthday.astimezone(TIMEZONE_MGA).year}},
                        {"header": "birthday", "value": birth.person.birthday.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": birth.person.birthday.astimezone(TIMEZONE_MGA)},
                        {"header": "father", "value": birth.father or birth.recognized_by or _("unknown"), "style": "text-start w-4 text-nowrap", "title": birth.father or birth.recognized_by or  _("unknown")},
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
def birth_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "birth"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    form = CERTIFICATE[menu_name]()

    cert_pk = int(request.POST.get('cert_pk', 0))

    person_pk = int(request.POST.get('person_pk', 0))

    number_initial = "1".zfill(2) if not BirthCertificate.objects.count() else str(BirthCertificate.objects.last().number + 1).zfill(2)

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
        form.fields['birthday'].initial = person.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if person.birthday else None
        form.fields['is_alive'].initial = person.is_alive

    if cert_pk > 0:
        # Une reconnaissance par le père
        certificate = BirthCertificate.objects.get(pk=cert_pk)
        request.session['person'] = certificate.person.pk
        # Matricule
        form.fields['fokotany'].initial = certificate.person.last_name
        form.fields['fokotany'].disabled =True
        number_initial = "1".zfill(2) if not RecognizationCertificate.objects.count() else str(RecognizationCertificate.objects.last().number + 1).zfill(2)
        # Information personnelle du mort
        form.fields['last_name'].initial = certificate.person.last_name
        form.fields['last_name'].disabled =True
        form.fields['first_name'].initial = certificate.person.first_name
        form.fields['first_name'].disabled =True
        form.fields['gender'].initial = certificate.person.gender
        form.fields['gender'].disabled =True
        form.fields['birth_place'].initial = certificate.person.birth_place
        form.fields['birth_place'].disabled =True
        form.fields['birthday'].initial = certificate.person.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.person.birthday else None
        form.fields['birthday'].disabled =True
        form.fields['is_alive'].initial = certificate.was_alive
        form.fields['is_alive'].disabled =True
        # Information du père
        form.fields['father_exist'].initial = True
        form.fields['father_exist'].disabled = True
        form.fields['father_last_name'].required = True
        form.fields['father_first_name'].required = False
        form.fields['father_birth_place'].required = True
        form.fields['father_birthday'].required = True
        form.fields['father_job'].required = True
        form.fields['father_address'].required = True
        form.fields['father_was_alive'].initial =True
        form.fields['father_was_alive'].disabled =True
        # Information du mère
        form.fields['mother_exist'].initial = True if certificate.mother else False
        form.fields['mother_exist'].disabled = True
        form.fields['mother_last_name'].initial = certificate.mother.last_name
        form.fields['mother_last_name'].disabled = True
        form.fields['mother_first_name'].initial = certificate.mother.first_name
        form.fields['mother_first_name'].disabled = True
        form.fields['mother_birth_place'].initial = certificate.mother.birth_place
        form.fields['mother_birth_place'].disabled = True
        form.fields['mother_birthday'].initial = certificate.mother.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.mother.birthday else None
        form.fields['mother_birthday'].disabled = True
        form.fields['mother_job'].initial = certificate.mother.carreer
        form.fields['mother_job'].disabled = True
        form.fields['mother_address'].initial = certificate.mother.address
        form.fields['mother_address'].disabled = True
        form.fields['mother_was_alive'].initial =certificate.mother.is_alive
        form.fields['mother_was_alive'].disabled =True
        # Information du déclarant
        form.fields['declarer_present'].initial = True if certificate.declarer else False
        form.fields['declarer_present'].disabled = True
        form.fields['declarer_last_name'].initial = certificate.declarer.last_name
        form.fields['declarer_last_name'].disabled = True
        form.fields['declarer_first_name'].initial = certificate.declarer.first_name
        form.fields['declarer_first_name'].disabled = True
        form.fields['declarer_gender'].initial = certificate.declarer.gender
        form.fields['declarer_gender'].disabled = True
        form.fields['declarer_birth_place'].initial = certificate.declarer.birth_place
        form.fields['declarer_birth_place'].disabled = True
        form.fields['declarer_birthday'].initial = certificate.declarer.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.declarer.birthday else None
        form.fields['declarer_birthday'].disabled = True
        form.fields['declarer_relation'].initial = certificate.declarer_relationship
        form.fields['declarer_relation'].disabled = True
        form.fields['declarer_job'].initial = certificate.declarer.carreer
        form.fields['declarer_job'].disabled = True
        form.fields['declarer_address'].initial = certificate.declarer.address
        form.fields['declarer_address'].disabled = True
        # Information sur l'enregistrement
        # form.fields['responsible'].initial = certificate.responsible_staff
        form.fields['declaration_date'].initial = (datetime.now() - timedelta(days=30)).astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")
        form.fields['register_date'].initial = datetime.now(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")

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

    if list(form.data.keys()).index('father_last_name') == 3:
        # Création de la person qui fait la reconnaissance s'il n'existe pas encore
        father, father_created = Person.objects.get_or_create(
            last_name = form.data['father_last_name'],
            first_name = form.data['father_first_name'],
            gender = 'M',
            birthday = form.data['father_birthday'],
            birth_place = form.data['father_birth_place'],
        )
        if father_created:
            messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': father.full_name})

        father.carreer = form.data['father_job']
        father.address = form.data['father_address']

        try:
            father.save()
            messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': father.full_name})
        except:
            messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': father.full_name})

        # Reconnaissance par le père
        person = Person.objects.get(pk=request.session['person'])
        number = int(request.POST['number'])
        try:
            certificate = RecognizationCertificate.objects.create(
                number = number,
                person = person,
                recognized_by = father,
                responsible_staff = Staff.objects.get(pk=form.data['responsible']),
                date_declaration = form.data['declaration_date'],
                date_register = form.data['register_date']
            )
            messages.success(request, _('Recognization Certificate Created Successfully !'))
        except:
            messages.error(request, _('Recognization Certificate Creation Error !'))

        request.session['certificate'] = 0

        request.session['type_cert'] = 'recognization'
        return redirect(certificate.get_preview_url())

    elif form.data:
        # Table Fokotany
        fokotany = Fokotany.objects.get(pk=form.fieldsets_fields[_('Matricule')][0].data)
        # Table Personne
        person, person_created = Person.objects.get_or_create(
            last_name = form.data['last_name'],
            first_name = form.data['first_name'],
            gender = form.data['gender'],
            birthday = None if form.data['birthday'] == "" else form.data['birthday'],
            birth_place = form.data['birth_place'],
        )
        if person_created:
            messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': person.full_name})

        person.is_alive = True if 'is_alive' in request.POST else False
        person.address = form.data['mother_address']

        try:
            person.save()
            messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': person.full_name})
        except:
            messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': person.full_name})

        if "do_certificate" in request.POST:
            print(form.data['do_certificate'])

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother, mother_created = Person.objects.get_or_create(
                    last_name = form.data['mother_last_name'],
                    first_name = form.data['mother_first_name'],
                    gender = 'F',
                    birthday = None if form.data['mother_birthday'] == "" else form.data['mother_birthday'],
                    birth_place = form.data['mother_birth_place'],
                )
                if mother_created:
                    messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': mother.full_name})
                print(mother)
                mother.carreer = form.data['mother_job']
                mother.address = form.data['mother_address']
                mother.is_alive = True if 'mother_was_alive' in request.POST else False
                
                if not mother.is_parent:
                    mother.is_parent = True

                try:
                    mother.save()
                    messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': mother.full_name})
                except:
                    messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': mother.full_name})

            # Si le père existe
            if 'father_exist' in request.POST:
                had_father = True
                father, father_created = Person.objects.get_or_create(
                    last_name = form.data['father_last_name'],
                    first_name = form.data['father_first_name'],
                    gender = 'M',
                    birthday = None if form.data['father_birthday'] == "" else form.data['father_birthday'],
                    birth_place = form.data['father_birth_place'],
                )
                if father_created:
                    messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': father.full_name})
                father.carreer = form.data['father_job']
                father.address = form.data['father_address']
                father.is_alive = True if 'father_was_alive' in request.POST else False

                if father.is_parent:
                    father.is_parent = True

                try:
                    father.save()
                    messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': father.full_name})
                except:
                    messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': father.full_name})
                    
            else:
                # Sans père
                father = None
                had_father = False

            # déclarant
            declarer, declarer_created = Person.objects.get_or_create(
                last_name = form.data['declarer_last_name'],
                first_name = form.data['declarer_first_name'],
                gender = form.data['declarer_gender'],
                birthday = form.data['declarer_birthday'],
                birth_place = form.data['declarer_birth_place'],
            )
            if declarer_created:
                messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': declarer.full_name})
            declarer.address = form.data['declarer_address']
            declarer.carreer = form.data['declarer_job']
            declarer.save()

            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = form.data['declarer_relation']
            date_declaration = form.data['declaration_date']
            date_register = form.data['register_date']
            responsible_staff = Staff.objects.get(pk=int(form.data['responsible']))
            number = int(form.data['number'])

            print(responsible_staff)

            if father and (father.birthday > person.birthday):
                messages.error(request, _("Father's Birthday Is Younger Than The Person."))
                return redirect('civil:birth-register')
            if (mother.birthday > person.birthday):
                messages.error(request, _("Mother's Birthday Is Younger Than The Person."))
                return redirect('civil:birth-register')

            # Table BirthCertificate
            if form.is_valid():
                certificate = BirthCertificate.objects.create(
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
                    date_declaration = date_declaration,
                    date_register = date_register,
                )
                messages.success(request, "BirthCertificate created successfully !")
                    
                # certificate_creation(request, menu_name, certificate.pk, many=1)
                request.session['type_cert'] = menu_name
                return redirect(certificate.get_preview_url())
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
    is_original = False
    responsible = None
    notes = ""

    print(request.GET)

    if request.session.get("type_cert", None):
        type_cert = request.session["type_cert"]
        is_original = True
        request.session["type_cert"] = None
        request.session.delete("type_cert")
    else:
        type_cert = request.GET.get('type_cert', None)

    many = int(request.GET.get('many_cp', 1))

    if request.GET.get("responsible", None):
        responsible = Staff.objects.get(pk=request.GET["responsible"])

    if ('client_detail' in request.GET and request.GET['client_detail'] != '') and ('client_gender' in request.GET and request.GET['client_gender'] != ''):
        notes = GENDER_CLIENT[request.GET['client_gender']] + " " + request.GET['client_detail']

    if '_doc' in type_cert:
        type_cert = type_cert.replace('_doc', "")
        is_doc = True

    menu_name = type_cert

    if is_doc:
        if type_cert == 'birth':
            document = BirthCertificateDocument.objects.get(pk=pk)
            print(document.date_register)
        elif type_cert == 'recognization':
            document = RecognizationCertificateDocument.objects.get(pk=pk)
        elif type_cert == 'marriage':
            document = MarriageCertificateDocument.objects.get(pk=pk) 
        elif type_cert == 'death':
            document = DeathCertificateDocument.objects.get(pk=pk)
    else:
        person = get_object_or_404(Person, pk=pk)
        if type_cert == 'birth':
            birth = get_object_or_404(BirthCertificate, person=person)
            if is_original:
                responsible = birth.responsible_staff
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
                person_is_alive = birth.person.is_alive,
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
                # Reconnaissance
                is_recognized = birth.is_recognized,
                recognized_by_last_name = birth.recognized_by.last_name if birth.recognized_by else None,
                recognized_by_first_name = birth.recognized_by.first_name if birth.recognized_by else None,
                recognization_numero = birth.recognization_numero if birth.is_recognized else None,
                date_recognization = birth.date_recognization if birth.is_recognized else None,
                # Enregistrement
                had_father = birth.had_father,
                was_alive = birth.was_alive,
                fokotany = birth.fokotany,
                responsible_staff_name = responsible.full_name,
                responsible_staff_role = responsible.role.title if Role.objects.get(service__grade=1, grade=1) == responsible.role else "Mpisolo toeran'i Ben'ny Tanàna",
                date_register = birth.date_register,
                status = 'D',
                num_copy = many,
                price = 0 if is_original else ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
                is_original = is_original,
            )

            message_success = _('Birth Document created successfully.')
            message_error = _('Birth Document Creation Errors.')
            
        elif type_cert == 'recognization':
            birth = BirthCertificate.objects.get(person=person)
            recognization = RecognizationCertificate.objects.get(person=person)
            if is_original:
                responsible = recognization.responsible_staff
            document = RecognizationCertificateDocument(
                certificate = recognization,
                number = recognization.number,
                # Person
                person_last_name = recognization.person.last_name,
                person_first_name = recognization.person.first_name,
                person_gender = recognization.person.gender,
                person_birth_place = recognization.person.birth_place,
                person_birthday = recognization.person.birthday,
                person_address = recognization.person.address,
                # Père
                father_last_name = recognization.recognized_by.last_name,
                father_first_name = recognization.recognized_by.first_name,
                father_birth_place = recognization.recognized_by.birth_place,
                father_birthday = recognization.recognized_by.birthday,
                father_carreer = recognization.recognized_by.carreer,
                father_address = recognization.recognized_by.address,
                # Mère
                mother_last_name = birth.mother.last_name,
                mother_first_name = birth.mother.first_name,
                mother_birth_place = birth.mother.birth_place,
                mother_birthday = birth.mother.birthday,
                mother_carreer = birth.mother.carreer,
                mother_address = birth.mother.address,
                mother_is_alive = birth.mother.is_alive,
                # register
                fokotany = birth.fokotany,
                responsible_staff_name = responsible.full_name,
                responsible_staff_role = responsible.role.title if Role.objects.get(service__grade=1, grade=1) == responsible.role else "Mpisolo toeran'i Ben'ny Tanàna",
                date_register = recognization.date_register,
                status = 'D',
                num_copy = many,
                price = 0 if is_original else ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
                is_original = is_original,
            )

            message_success = _('Recognization Document created successfully.')
            message_error = _('Recognization Document Creation Errors.')

        elif type_cert == 'marriage':
            marriage = person.marriage_certificate
            if is_original:
                responsible = marriage.responsible_staff
            document = MarriageCertificateDocument(
                certificate = marriage,
                number = marriage.number,
                # Le marié
                groom_last_name = marriage.groom.last_name,
                groom_first_name = marriage.groom.first_name,
                groom_birth_place = marriage.groom.birth_place,
                groom_birthday = marriage.groom.birthday,
                groom_carreer = marriage.groom.carreer,
                groom_address = marriage.groom.address,
                groom_nationality = marriage.groom.nationality,
                # La mariée
                bride_last_name = marriage.bride.last_name,
                bride_first_name = marriage.bride.first_name,
                bride_birth_place = marriage.bride.birth_place,
                bride_birthday = marriage.bride.birthday,
                bride_carreer = marriage.bride.carreer,
                bride_address = marriage.bride.address,
                bride_nationality = marriage.bride.nationality,
                # Père du marié
                father_groom_last_name = marriage.father_groom.last_name if marriage.father_groom else None,
                father_groom_first_name = marriage.father_groom.first_name if marriage.father_groom else None,
                father_groom_birth_place = marriage.father_groom.birth_place if marriage.father_groom else None,
                father_groom_birthday = marriage.father_groom.birthday if marriage.father_groom else None,
                father_groom_carreer = marriage.father_groom.carreer if marriage.father_groom else None,
                father_groom_address = marriage.father_groom.address if marriage.father_groom else None,
                father_groom_is_alive = marriage.father_groom.is_alive if marriage.father_groom else False,
                # Père de la mariée
                father_bride_last_name = marriage.father_bride.last_name if marriage.father_bride else None,
                father_bride_first_name = marriage.father_bride.first_name if marriage.father_bride else None,
                father_bride_birth_place = marriage.father_bride.birth_place if marriage.father_bride else None,
                father_bride_birthday = marriage.father_bride.birthday if marriage.father_bride else None,
                father_bride_carreer = marriage.father_bride.carreer if marriage.father_bride else None,
                father_bride_address = marriage.father_bride.address if marriage.father_bride else None,
                father_bride_is_alive = marriage.father_bride.is_alive if marriage.father_bride else False,
                # Mère du marié
                mother_groom_last_name = marriage.mother_groom.last_name if marriage.mother_groom else None,
                mother_groom_first_name = marriage.mother_groom.first_name if marriage.mother_groom else None,
                mother_groom_birth_place = marriage.mother_groom.birth_place if marriage.mother_groom else None,
                mother_groom_birthday = marriage.mother_groom.birthday if marriage.mother_groom else None,
                mother_groom_carreer = marriage.mother_groom.carreer if marriage.mother_groom else None,
                mother_groom_address = marriage.mother_groom.address if marriage.mother_groom else None,
                mother_groom_is_alive = marriage.mother_groom.is_alive if marriage.mother_groom else False,
                # Mère de la mariée
                mother_bride_last_name = marriage.mother_bride.last_name if marriage.mother_bride else None,
                mother_bride_first_name = marriage.mother_bride.first_name if marriage.mother_bride else None,
                mother_bride_birth_place = marriage.mother_bride.birth_place if marriage.mother_bride else None,
                mother_bride_birthday = marriage.mother_bride.birthday if marriage.mother_bride else None,
                mother_bride_carreer = marriage.mother_bride.carreer if marriage.mother_bride else None,
                mother_bride_address = marriage.mother_bride.address if marriage.mother_bride else None,
                mother_bride_is_alive = marriage.mother_bride.is_alive if marriage.mother_bride else False,
                # Témoins du marié
                witness_groom_first_name = marriage.witness_groom.first_name,
                witness_groom_last_name = marriage.witness_groom.last_name,
                witness_groom_gender = marriage.witness_groom.gender,
                witness_groom_birth_place = marriage.witness_groom.birth_place,
                witness_groom_birthday = marriage.witness_groom.birthday,
                witness_groom_carreer = marriage.witness_groom.carreer,
                witness_groom_address = marriage.witness_groom.address,
                # Témoins de la mariée
                witness_bride_first_name = marriage.witness_bride.first_name,
                witness_bride_last_name = marriage.witness_bride.last_name,
                witness_bride_gender = marriage.witness_bride.gender,
                witness_bride_birth_place = marriage.witness_bride.birth_place,
                witness_bride_birthday = marriage.witness_bride.birthday,
                witness_bride_carreer = marriage.witness_bride.carreer,
                witness_bride_address = marriage.witness_bride.address,
                # Mariage
                wedding_day = marriage.wedding_day,
                # Enregistrement
                fokotany = marriage.fokotany,
                responsible_staff_name = responsible.full_name,
                responsible_staff_role = responsible.role.title if Role.objects.get(service__grade=1, grade=1) == responsible.role else "Mpisolo toeran'i Ben'ny Tanàna",
                date_register = marriage.date_register,
                status = 'D',
                num_copy = many,
                price = 0 if is_original else ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
                is_original = is_original,
            )

            message_success = _('Marriage Document created successfully.')
            message_error = _('Marriage Document Creation Errors.')
            
        elif type_cert == 'death':
            print("DEATH !!!!!!!!!")
            death = DeathCertificate.objects.get(person=person)
            if is_original:
                responsible = death.responsible_staff
            document = DeathCertificateDocument(
                certificate = death,
                number = death.number,
                # Person
                person_last_name = death.person.last_name,
                person_first_name = death.person.first_name if death.person else "",
                person_birth_place = death.person.birth_place if death.person else "",
                person_birthday = death.person.birthday if death.person else None,
                person_carreer = death.person.carreer if death.person else "",
                person_address = death.person.address if death.person else "",
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
                responsible_staff_name = responsible.full_name,
                responsible_staff_role = responsible.role.title if Role.objects.get(service__grade=1, grade=1) == responsible.role else "Mpisolo toeran'i Ben'ny Tanàna",
                date_register = death.date_register,
                date_created = datetime.now(),
                status = 'D',
                num_copy = many,
                price = 0 if is_original else ServicePrice.objects.get(pk=1).certificate_price,
                notes = notes,
                is_original = is_original,
            )

            message_success = _('Death Document Created Successfully.')
            message_error = _('Death Document Creation Errors.')

        try:
            document.save()
            messages.success(request, message_success)
        except IntegrityError:
            messages.error(request, message_error)
            return redirect(person.url_detail)

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

    print(menu)

    try:
        if menu == 'birth':
            document = get_object_or_404(BirthCertificateDocument, pk=pk)
            document.date_validated = datetime.now()
            document.validated_by = Staff.objects.get(role__access=request.user) if Staff.objects.filter(role__access=request.user) else None
            document.status = "V"
        elif menu == 'recognization':
            document = get_object_or_404(RecognizationCertificateDocument, pk=pk)
            document.date_validated = datetime.now()
            document.validated_by = Staff.objects.get(role__access=request.user) if Staff.objects.filter(role__access=request.user) else None
            document.status = "V"
        elif menu == 'marriage':
            document = get_object_or_404(MarriageCertificateDocument, pk=pk)
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
        return JsonResponse({'error': 'Document not found'}, status=404)

@login_required
def certificate_deletion(request: WSGIRequest, menu:str, pk:int):
    """Valider un certificat"""


    if '_doc' in menu:
        menu = menu.replace('_doc', '')

    if menu == "birth":
        document = get_object_or_404(BirthCertificateDocument, pk=pk)
        person = document.certificate.person.pk
    if menu == "recognization":
        document = get_object_or_404(RecognizationCertificateDocument, pk=pk)
        person = document.certificate.person.pk
    if menu == "marriage":
        document = get_object_or_404(MarriageCertificateDocument, pk=pk)
    if menu == "death":
        document = get_object_or_404(DeathCertificateDocument, pk=pk)
        person = document.certificate.person.pk
    
    if document.can_delete:
        response = document.delete()
        print(response)
        messages.success(request, _('Certificate deleted successfully.'))
    else:
        messages.error(request, _('This certificate cannot be deleted.'))
    
    if menu == "birth" or menu == "recognization" or (menu == 'death' and BirthCertificate.objects.filter(person_id=person)):
        return redirect(__package__+':person-detail', person)
    else:
        return redirect(__package__+':'+menu)

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
            {"name": "father", "header": _("father"), "db_col_name": "father__last_name", "type": "search", "query": ["father__last_name__icontains", "father__first_name__icontains"]},
            {"name": "mother", "header": _("mother"), "db_col_name": "mother__last_name", "type": "search", "query": ["mother__last_name__icontains", "mother__first_name__icontains"]},
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
                        else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                        if headers[index_search]['name'] == 'date'
                        else request.GET['q']
        )
        certificates_data = certificates_data.filter(
                    Q(**{f"{headers[index_search]['query'][0]}":request.GET['q']}) |
                    Q(**{f"{headers[index_search]['query'][1]}":request.GET['q']})
                    if len(headers[index_search]['query']) == 2
                    else
                    Q(
                        **{
                            f"{headers[index_search]['query'][0]}":
                            date.today() - timedelta(days=int(request.GET['q'])*365) 
                            if headers[index_search]['name'] in ['age', 'lived'] 
                            else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                            if headers[index_search]['name'] == 'date'
                            else True if request.GET['q'] == '0' else False
                            if headers[index_search]['name'] == 'birth'
                            else request.GET['q']
                           }
                        )

                )

    # Ordre
    ordered = 'order' in list(request.GET) and request.GET['order'] != ''
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
        order_changed = request.GET['order'] != request.session['order_name']
        # Clic sur l'une des colonnes
        order_sense_changeable = request.GET['order'] in [header['name'] + '_touched' for header in headers]
        if order_sense_changeable:
            print('COLONNE CLIQUEE !!!!!!!!!!!')
            # identification de la colonne
            column = request.GET['order'].replace('_touched', '')
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
                break
    else:
        certificates_data = certificates_data.order_by("pk").reverse()

    # Pagination
    certificate_bypage = Paginator(certificates_data, line_bypage)

    n_page = int(request.GET.get('num_page', 1))

    if "paging" in list(request.GET.keys()) and n_page in (int(request.GET['paging']) + 1, int(request.GET['paging']) - 1) and int(request.GET['paging']) in certificate_bypage.page_range:
        n_page = int(request.GET['paging'])
        
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
            "datas": [
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
                        {"header": "father", "value": death.person.father or _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.person.father or _("unknown")},
                        {"header": "mother", "value": death.person.mother or _("unknown"), "style": "text-start w-4 text-nowrap", "title": death.person.mother or _("unknown")},
                        {"header": "fokotany", "value": death.fokotany.name, "style": "text-start w-4 text-nowrap", "title": death.fokotany},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": "open", "title": _("open"), "style": "blue"},
                            # {"name": "print", "title": _("print"), "style": "blue"},
                            {"name": "delete", "title": _("delete"), "style": "red"},
                        ]},
                    ],
                } for index, death in enumerate(certificate_page)
            ]
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

    print(request.POST)

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
        form.fields['birthday'].initial = person.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if person.birthday else None
        form.fields['dead_job'].initial = person.carreer
        form.fields['dead_address'].initial = person.address
        # Si la personne a déjà un certificat de naissance
        certificate = BirthCertificate.objects.filter(person=person)
        if certificate:
            certificate = certificate.first()
            # Information du père
            form.fields['father_exist'].initial = True if certificate.father else False
            form.fields['father_last_name'].initial = certificate.father.last_name if certificate.father else None
            form.fields['father_first_name'].initial = certificate.father.first_name if certificate.father else None
            form.fields['father_birth_place'].initial = certificate.father.birth_place if certificate.father else None
            form.fields['father_birthday'].initial = certificate.father.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.father else None
            form.fields['father_address'].initial = certificate.father.address if certificate.father else None
            form.fields['father_job'].initial = certificate.father.carreer if certificate.father else None
            form.fields['father_was_alive'].initial = certificate.father.is_alive if certificate.father else False
            # Information du mère
            form.fields['mother_exist'].initial = True if certificate.mother else False
            form.fields['mother_last_name'].initial = certificate.mother.last_name if certificate.mother else None
            form.fields['mother_first_name'].initial = certificate.mother.first_name if certificate.mother else None
            form.fields['mother_birth_place'].initial = certificate.mother.birth_place if certificate.mother else None
            form.fields['mother_birthday'].initial = certificate.mother.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.mother else None
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
        form.fields['birthday'].initial = certificate.person.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")
        form.fields['dead_address'].initial = certificate.person.address
        form.fields['dead_job'].initial = certificate.person.carreer
        # Information du père
        form.fields['father_exist'].initial = True if certificate.father else False
        form.fields['father_last_name'].initial = certificate.father.last_name if certificate.father else None
        form.fields['father_first_name'].initial = certificate.father.first_name if certificate.father else None
        form.fields['father_birth_place'].initial = certificate.father.birth_place if certificate.father else None
        form.fields['father_birthday'].initial = certificate.father.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.father and certificate.father.birthday else None
        form.fields['father_address'].initial = certificate.father.address if certificate.father else None
        form.fields['father_job'].initial = certificate.father.carreer if certificate.father else None
        form.fields['father_was_alive'].initial = certificate.father.is_alive if certificate.father else None
        # Information du mère
        form.fields['mother_exist'].initial = True if certificate.mother else False
        form.fields['mother_last_name'].initial = certificate.mother.last_name if certificate.mother else None
        form.fields['mother_first_name'].initial = certificate.mother.first_name if certificate.mother else None
        form.fields['mother_birth_place'].initial = certificate.mother.birth_place if certificate.mother else None
        form.fields['mother_birthday'].initial = certificate.mother.birthday.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M") if certificate.mother and certificate.mother.birthday else None
        form.fields['mother_address'].initial = certificate.mother.address if certificate.mother else None
        form.fields['mother_job'].initial = certificate.mother.carreer if certificate.mother else None
        form.fields['mother_was_alive'].initial = certificate.mother.is_alive if certificate.mother else None
        # Information sur l'enregistrement
        form.fields['declaration_date'].initial = certificate.date_declaration.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")
        form.fields['register_date'].initial = certificate.date_register.astimezone(TIMEZONE_MGA).__format__("%Y-%m-%d %H:%M")
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
        print(form.data['birthday'])
        person, person_created = Person.objects.get_or_create(
                    last_name = form.data['last_name'],
                    first_name = form.data['first_name'],
                    gender = form.data['gender'],
                    birthday = form.data['birthday'] if form.data['birthday'] != '' else None,
                    birth_place = form.data['birth_place'],
                )
        
        print(person)

        if "do_certificate" in request.POST:
            print(form.data['do_certificate'])

            # Information complémentaire du décédé
            death_place = form.data['death_place']
            death_day = form.data['death_day']
            person.carreer = request.POST.get('dead_job')
            person.address = request.POST.get('dead_address')
            person.save()

            # Si la mère existe
            if "mother_exist" in request.POST:
                mother = Person.objects.get_or_create(
                    last_name = form.data['mother_last_name'],
                    first_name = form.data['mother_first_name'],
                    gender = 'F',
                    birthday =  form.data['mother_birthday'] if form.data['mother_birthday'] != '' else None,
                    birth_place = form.data['mother_birth_place'],
                )[0]
                print(mother)
                mother.is_alive = True if "father_was_alive" in request.POST else False
                mother.carreer = form.data['mother_job']
                mother.address = form.data['mother_address']
                mother.save()
            else:
                # Sans père
                mother = None

            # Si le père existe
            if 'father_exist' in request.POST:
                father = Person.objects.get_or_create(
                    last_name = form.data['father_last_name'],
                    first_name = form.data['father_first_name'],
                    gender = 'M',
                    birthday =  form.data['father_birthday'] if form.data['father_birthday'] != '' else None,
                    birth_place = form.data['father_birth_place'],
                )[0]
                father.is_alive = True if "mother_was_alive" in request.POST else False
                father.carreer = form.data['father_job']
                father.address = form.data['father_address']
                father.save()
            else:
                # Sans père
                father = None

            # déclarant
            declarer = Person.objects.get_or_create(
                last_name = form.data['declarer_last_name'],
                first_name = form.data['declarer_first_name'],
                gender = form.data['declarer_gender'],
                birthday = form.data['declarer_birthday'],
                birth_place = form.data['declarer_birth_place'],
            )[0]
            declarer.carreer = form.data['declarer_job']
            declarer.address = form.data['declarer_address']
            declarer.save()

            declarer_was_present = True if 'declarer_present' in request.POST else False
            declarer_relationship = form.data['declarer_relation']
            date_declaration = form.data['declaration_date']
            date_register = form.data['register_date']
            responsible_pk = form.data['responsible']
            number = int(request.POST['number'])

            # Table BirthCertificate
            if form.is_valid():
                try:
                    certificate = DeathCertificate.objects.create(
                        number = number,
                        person = person,
                        father = father,
                        mother = mother,
                        declarer = declarer,
                        declarer_relationship = declarer_relationship,
                        declarer_was_present = declarer_was_present,
                        responsible_staff = Staff.objects.get(pk=responsible_pk),
                        fokotany = fokotany,
                        death_day = death_day,
                        death_place = death_place,
                        date_declaration = date_declaration,
                        date_register = date_register,
                    )
        
                    if person.is_alive:
                        person.is_alive = False
                        person.save(update_fields=["is_alive"])

                    request.session['type_cert'] = menu_name
                    return redirect(certificate.get_preview_url())
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
def death_delete(request: WSGIRequest, death_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    print("DEATH SUPPR !!!!!!!!!")
    try:
        certificate = DeathCertificate.objects.get(pk=death_id)
        full_name = certificate.person.full_name
        
        certificate.delete()

        messages.success(request, _('The Certificate of %(name)s deleted successfully.')%{'name': full_name})
    except:
        messages.error(request, _('This certificate cannot be deleted.'))
        ...

    return redirect('civil:death')

@login_required
def marriage(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    headers = [
            {"name": "date", "header": _("date"), "db_col_name": "date_register", "type": "date", "query": ["date_register__date"]},
            {"name": "number", "header": _("number"), "db_col_name": "number", "type": "number", "query": ["number"]},
            {"name": "groom", "header": _("groom"), "db_col_name": "groom__last_name" if get_language() == 'mg' else "groom__first_name", "type": "search", "query": ["groom__last_name__icontains", "groom__first_name__icontains"]},
            {"name": "bride", "header": _("bride"), "db_col_name": "bride__last_name" if get_language() == 'mg' else "bride__first_name", "type": "search", "query": ["bride__last_name__icontains", "bride__first_name__icontains"]},
            {"name": "wedding_day", "header": _("wedding day"), "db_col_name": "wedding_day", "type": "date", "query": ["wedding_day"]},
            {"name": "father_groom", "header": _("father of groom"), "db_col_name": "father_groom__last_name" if get_language() == 'mg' else "father_groom__first_name", "type": "search", "query": ["father_groom__last_name__icontains", "father_groom__first_name__icontains"]},
            {"name": "mother_groom", "header": _("mother of groom"), "db_col_name": "mother_groom__last_name" if get_language() == 'mg' else "mother_groom__first_name", "type": "search", "query": ["mother_groom__last_name__icontains", "mother_groom__first_name__icontains"]},
            {"name": "father_bride", "header": _("father of bride"), "db_col_name": "father_bride__last_name" if get_language() == 'mg' else "father_bride__first_name", "type": "search", "query": ["father_bride__last_name__icontains", "father_bride__first_name__icontains"]},
            {"name": "mother_bride", "header": _("mother of bride"), "db_col_name": "mother_bride__last_name" if get_language() == 'mg' else "mother_bride__first_name", "type": "search", "query": ["mother_bride__last_name__icontains", "mother_bride__first_name__icontains"]},
            {"name": "witness_groom", "header": _("witness of groom"), "db_col_name": "witness_groom__last_name" if get_language() == 'mg' else "witness_groom__first_name", "type": "search", "query": ["witness_groom__last_name__icontains", "witness_groom__first_name__icontains"]},
            {"name": "witness_bride", "header": _("witness of bride"), "db_col_name": "witness_bride__last_name" if get_language() == 'mg' else "witness_bride__first_name", "type": "search", "query": ["witness_bride__last_name__icontains", "witness_bride__first_name__icontains"]},
            {"name": "active", "header": _("active"), "db_col_name": "is_active", "type": "select", "query": ["is_active"], 'select': {'0': _('active').capitalize(), '1': _('not active').capitalize()}},
            {"name": "fokotany", "header": _("fokotany"), "db_col_name": "fokotany", "type": "search", "query": ["fokotany__name__icontains"]},
            {"name": "action", "header": _("action"), "db_col_name": "", "type": "", "query": []},
        ]

    add_action_url(__package__, menu_name)

    line_bypage = str(request.GET.get('line', 50))

    # Tous les Certificats
    certificates_data = MarriageCertificate.objects.all()

    # Recherche
    index_search = int(request.GET.get('search_filter', 3))

    is_searching = False

    if 'q' in request.GET.keys() and request.GET['q'] != "":
        is_searching = True
        print(headers[index_search])
        print(
        date.today() - timedelta(days=int(request.GET['q'])*365) 
                        if headers[index_search]['name'] == 'age'
                        else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                        if headers[index_search]['name'] == 'date'
                        else request.GET['q']
        )

        certificates_data = certificates_data.filter(
                    Q(**{f"{headers[index_search]['query'][0]}":request.GET['q']}) |
                    Q(**{f"{headers[index_search]['query'][1]}":request.GET['q']})
                    if len(headers[index_search]['query']) == 2
                    else
                    Q(
                        **{
                            f"{headers[index_search]['query'][0]}": 
                            date.today() - timedelta(days=int(request.GET['q'])*365) 
                            if headers[index_search]['name'] == 'age'
                            else date(int(request.GET['q'].split('-')[0]), int(request.GET['q'].split('-')[1]), int(request.GET['q'].split('-')[2]))
                            if headers[index_search]['name'] == 'date' 
                            else True if request.GET['q'] == '0' else False
                            if headers[index_search]['name'] == 'birth'
                            else request.GET['q']
                           }
                        )
                )

    # Ordre
    ordered = 'order' in list(request.GET) and request.GET['order'] != ''
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
        order_changed = request.GET['order'] != request.session['order_name']
        # Clic sur l'une des colonnes
        order_sense_changeable = request.GET['order'] in [header['name'] + '_touched' for header in headers]
        if order_sense_changeable:
            # print('COLONNE CLIQUEE !!!!!!!!!!!')
            # identification de la colonne
            column = request.GET['order'].replace('_touched', '')
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

    if "paging" in list(request.GET.keys()) and n_page in (int(request.GET['paging']) + 1, int(request.GET['paging']) - 1) and int(request.GET['paging']) in certificate_bypage.page_range:
        n_page = int(request.GET['paging'])
        
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
            "datas": [
                {                                
                    "index" : index,
                    "certificate": marriage, 
                    "row": [
                        {"header": "date", "value": format(marriage.date_register.astimezone(TIMEZONE_MGA),'%d/%m/%Y'), "style": "text-center w-4 text-nowrap", "title": marriage.date_register},
                        {"header": "number", "value": "N° " + str(marriage.number), "style": "text-center w-12 text-nowrap", "title": "N° " + str(marriage.number)},
                        {"header": "groom", "value": marriage.groom, "style": "text-start w-4 text-nowrap", "title": marriage.groom},
                        {"header": "bride", "value": marriage.bride, "style": "text-start w-4 text-nowrap", "title": marriage.bride},
                        {"header": "wedding_day", "value": marriage.wedding_day.astimezone(TIMEZONE_MGA), "style": "text-start w-4 text-nowrap", "title": marriage.wedding_day.astimezone(TIMEZONE_MGA)},
                        {"header": "father_groom", "value": marriage.father_groom or marriage.groom.recognized_by or _("unknown"), "style": "text-start w-4 text-nowrap", "title": marriage.father_groom or marriage.groom.recognized_by or  _("unknown")},
                        {"header": "mother_groom", "value": marriage.mother_groom or _("unknown"), "style": "text-start w-4 text-nowrap", "title": marriage.mother_groom or _("unknown")},
                        {"header": "father_bride", "value": marriage.father_bride or marriage.bride.recognized_by or _("unknown"), "style": "text-start w-4 text-nowrap", "title": marriage.father_bride or marriage.bride.recognized_by or  _("unknown")},
                        {"header": "mother_bride", "value": marriage.mother_bride or _("unknown"), "style": "text-start w-4 text-nowrap", "title": marriage.mother_bride or _("unknown")},
                        {"header": "witness_groom", "value": marriage.witness_groom, "style": "text-start w-4 text-nowrap", "title": marriage.witness_groom},
                        {"header": "witness_bride", "value": marriage.witness_bride, "style": "text-start w-4 text-nowrap", "title": marriage.witness_bride},
                        {"header": "active", "value": _("active") if marriage.is_active else _("not active"), "style": "text-center w-4 text-nowrap", "title": _("active") if marriage.is_active else _("not active")},
                        {"header": "fokotany", "value": marriage.fokotany.name, "style": "text-start w-4 text-nowrap", "title": marriage.fokotany},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": "open", "title": _("open"), "url": "civil:person-detail", "style": "blue"},
                            # {"name": "print", "title": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            {"name": "delete", "title": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, marriage in enumerate(certificate_page)
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

    return render(request, "civil/list.html", context)

@login_required
def marriage_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    add_action_url(__package__, menu_name)

    form = CERTIFICATE[menu_name]()

    number_initial = "1".zfill(2) if not MarriageCertificate.objects.count() else str(MarriageCertificate.objects.last().number + 1).zfill(2)

    context = {
        "accessed": __package__ in request.session['app_accessed'],
        "app_home": __package__ + ":index",
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": form,
        "number_initial": number_initial,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "url_save": reverse("civil:marriage-save"),
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
def marriage_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    
    menu_name = 'marriage'

    # print(request.POST.keys())
        
    form = MarriageCertificateForm(request.POST)

    print(form.data)
    
    if form.data:
        # Table Fokotany
        fokotany = Fokotany.objects.get(pk=form.fieldsets_fields[_('Matricule')][0].data)
        # Table Personne
        ## Le marié
        groom, groom_created = Person.objects.get_or_create(
            last_name = form.data['groom_last_name'],
            first_name = form.data['groom_first_name'],
            gender = 'M',
            birthday = None if form.data['groom_birthday'] == "" else form.data['groom_birthday'],
            birth_place = form.data['groom_birth_place'],
        )
        if groom_created:
            messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': groom.full_name})

        groom.is_alive = True
        groom.carreer = form.data['groom_job']
        groom.address = form.data['groom_address']

        try:
            groom.save()
            messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': groom.full_name})
        except:
            messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': groom.full_name})
            
        ## La mariée
        bride, bride_created = Person.objects.get_or_create(
            last_name = form.data['bride_last_name'],
            first_name = form.data['bride_first_name'],
            gender = 'F',
            birthday = None if form.data['bride_birthday'] == "" else form.data['bride_birthday'],
            birth_place = form.data['bride_birth_place'],
        )
        if bride_created:
            messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': bride.full_name})

        bride.is_alive = True
        bride.carreer = form.data['bride_job']
        bride.address = form.data['bride_address']

        try:
            bride.save()
            messages.success(request, _('Person "%(name)s" Updated Successfully !')%{'name': bride.full_name})
        except:
            messages.error(request, _('Person "%(name)s" Modification Error !')%{'name': bride.full_name})

        if "do_certificate" in request.POST:
            # Si la mère du marié existe
            if "mother_groom_exist" in request.POST:
                if form.data.get("mother_groom_pk"):
                    print("Groom's mother existe dans la base de donnée")
                    mother_groom = Person.objects.get(pk=form.data.get("mother_groom_pk"))

                    if mother_groom and (mother_groom.birthday > groom.birthday):
                        messages.error(request, _("Groom's Mother Is Younger Than The Person."))
                        return redirect('civil:marriage-register')
                else:
                    print("Groom's mother n'existe pas dans la base de donnée")
                    mother_groom, mother_groom_exists = Person.objects.get_or_create(
                        last_name = form.data['mother_groom_last_name'],
                        first_name = form.data['mother_groom_first_name'],
                        gender = 'F',
                        address = form.data['mother_groom_address'],
                        is_alive = form.data['mother_groom_was_alive'],
                    )
            # Si la père du marié existe
            if "father_groom_exist" in request.POST:
                if form.data.get("father_groom_pk"):
                    print("Groom's father existe dans la base de donnée")
                    father_groom = Person.objects.get(pk=form.data.get("father_groom_pk"))

                    if father_groom and (father_groom.birthday > groom.birthday):
                        messages.error(request, _("Groom's Father Is Younger Than The Person."))
                        return redirect('civil:marriage-register')
                else:
                    print("Groom's father n'existe pas dans la base de donnée")
                    father_groom, father_groom_exist = Person.objects.get_or_create(
                        last_name = form.data['father_groom_last_name'],
                        first_name = form.data['father_groom_first_name'],
                        gender = 'M',
                        address = form.data['father_groom_address'],
                        is_alive = form.data['father_groom_was_alive'],
                    )
            # Si la mère de la mariée existe
            if "father_bride_exist" in request.POST:
                if form.data.get("mother_bride_pk"):
                    print("Bride's mother existe dans la base de donnée")
                    mother_bride = Person.objects.get(pk=form.data.get("mother_bride_pk"))

                    if mother_bride and (mother_bride.birthday > bride.birthday):
                        messages.error(request, _("Bride's Mother Is Younger Than The Person."))
                        return redirect('civil:marriage-register')
                else:
                    print("Bride's mother n'existe pas dans la base de donnée")
                    mother_bride, mother_bride_exists = Person.objects.get_or_create(
                        last_name = form.data['mother_bride_last_name'],
                        first_name = form.data['mother_bride_first_name'],
                        gender = 'F',
                        address = form.data['mother_bride_address'],
                        is_alive = form.data['mother_bride_was_alive'],
                    )
            # Si la père de la mariée existe
            if "father_bride_exist" in request.POST:
                if form.data.get("father_bride_pk"):
                    print("Bride's father existe dans la base de donnée")
                    father_bride = Person.objects.get(pk=form.data.get("father_bride_pk"))

                    if father_bride and (father_bride.birthday > bride.birthday):
                        messages.error(request, _("Bride's Father Is Younger Than The Person."))
                        return redirect('civil:marriage-register')
                else:
                    print("Bride's father n'existe pas dans la base de donnée")
                    father_bride, father_bride_exists = Person.objects.get_or_create(
                        last_name = form.data['father_bride_last_name'],
                        first_name = form.data['father_bride_first_name'],
                        gender = 'M',
                        address = form.data['father_bride_address'],
                        is_alive = form.data['father_bride_was_alive'],
                    )

            # témoins du marié
            witness_groom, witness_groom_created = Person.objects.get_or_create(
                last_name = form.data['witness_groom_last_name'],
                first_name = form.data['witness_groom_first_name'],
                gender = form.data['witness_groom_gender'],
                birthday = form.data['witness_groom_birthday'],
                birth_place = form.data['witness_groom_birth_place'],
            )
            if witness_groom_created:
                messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': witness_groom.full_name})
            witness_groom.address = form.data['witness_groom_address']
            witness_groom.carreer = form.data['witness_groom_job']
            witness_groom.save()

            # témoins de la mariée
            witness_bride, witness_bride_created = Person.objects.get_or_create(
                last_name = form.data['witness_bride_last_name'],
                first_name = form.data['witness_bride_first_name'],
                gender = form.data['witness_bride_gender'],
                birthday = form.data['witness_bride_birthday'],
                birth_place = form.data['witness_bride_birth_place'],
            )
            if witness_bride_created:
                messages.success(request, _('Person "%(name)s" Created Successfully !')%{'name': witness_bride.full_name})
            witness_bride.address = form.data['witness_bride_address']
            witness_bride.carreer = form.data['witness_bride_job']
            witness_bride.save()

            # Enregistrement
            print(form.data['wedding_day'])
            wedding_day = form.data['wedding_day']
            date_declaration = form.data['declaration_date']
            date_register = form.data['register_date']
            responsible_staff = Staff.objects.get(pk=int(form.data['responsible']))
            number = int(request.POST['number'])

            # Table MarriageCertificate
            if form.is_valid():
                certificate = MarriageCertificate.objects.create(
                    number = number,
                    groom = groom,
                    bride = bride,
                    father_groom = father_groom,
                    mother_groom = mother_groom,
                    father_bride = father_bride,
                    mother_bride = mother_bride,
                    witness_groom = witness_groom,
                    witness_bride = witness_bride,
                    responsible_staff = responsible_staff,
                    fokotany = fokotany,
                    is_active = True,
                    wedding_day = wedding_day,
                    date_declaration = date_declaration,
                    date_register = date_register,
                )
                messages.success(request, "Marriage's Certificate created successfully !")
                
                request.session['type_cert'] = menu_name
                return redirect(certificate.get_preview_url())
            else:
                messages.error(request, "Marriage's Certificate Creation Error:" + form.errors.as_text())

        return redirect('civil:marriage-register')
    ...

@login_required
def marriage_delete(request: WSGIRequest, marriage_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    print("MARRIAGE SUPPR !!!!!!!!!")
    try:
        certificate = MarriageCertificate.objects.get(pk=marriage_id)
        groom = certificate.groom.full_name
        bride = certificate.bride.full_name
        
        certificate.delete()

        messages.success(request, _('The Certificate of %(groom)s and %(bride)s deleted successfully.')%{'groom': groom, 'bride': bride})
    except:
        messages.error(request, _('This certificate cannot be deleted.'))
        ...

    return redirect('civil:marriage')

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