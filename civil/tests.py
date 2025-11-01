from decimal import Decimal
import json
from django.db import models
from datetime import datetime, timedelta, timezone
from itertools import chain
from operator import attrgetter
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.test import TestCase
from django.db.models import Sum, Count
from django.db.models.functions import TruncYear, TruncMonth

from administration.models import Common, Fokotany, Role, Staff 
from django.db.models import Q
from civil import views
from civil.forms import BirthCertificateForm
from civil.models import DeathCertificate, MarriageCertificate, Person, BirthCertificate
from django.utils.translation import activate, get_language, get_language_info
from django.utils.translation import gettext as _

from civil.templatetags.isa_gasy import OraGasy

# Create your tests here.

PERSONS = [
    ["Kenn Keren", "BEZARA", "M", datetime(2001,8,13,20), "ANTSIRANANA I", False],
    ["Kemuel Kelub", "BEZARA", "M", datetime(2004,7,1,14,30), "ANTSIRANANA I", False],
    ["Benoît Sydonie", "FENO", "F", datetime(1981,8,15,00,00), "ANTSIRANANA I", True],
]

def add_person():
    for person in PERSONS:
        try:
            Person.objects.create(
                first_name = person[0],
                last_name = person[1],
                gender = person[2],
                birthday = person[3],
                birth_place = person[4],
                is_parent = person[5]
            )
        except IntegrityError:            
            pass

def add_cert_birth():
    BirthCertificate.objects.create(
        certificate_type = "F",
        fokotany = Fokotany.objects.get(pk=2),
        born = Person.objects.get(pk=1),
        mother = Person.objects.get(pk=3),
        mother_carreer = "Femme au Foyer",
        mother_address = "Lot 3-206-14, Soafeno",
    )
    ...

# add_person()
# add_cert_birth()

# table = {
#             "headers": ["Nom", "Prénom", "Genre", "Âge"], 
#             "rows": [
#                 {
#                     "index" : index,
#                     "id": certificate.pk,
#                     "row": [
#                         {"last_name": certificate.birth_certificate.born.last_name, "style": ""},
#                         {"first_name": certificate.birth_certificate.born.first_name, "style": ""},
#                         {"gender": Person.GENDER_CHOICES[certificate.birth_certificate.born.gender], "style": ""},
#                         {"age": datetime.today().year - certificate.birth_certificate.born.birthday.year, "style": ""},
#                     ],
#                 } for index, certificate in enumerate(CertificateDocument.objects.all())
#             ],
#         }



# for row in table['rows']:
#     print(row['index'], row['id'], row['row'])


activate('mg')


# document = get_object_or_404(CertificateDocument, pk=1)

# print(BirthCertificate.objects.all().filter(
#     Q(**{"born__birthday__lte": datetime.today() - timedelta(days=18*365)})
# ))

# print(datetime.now() - timedelta(days=1))

# print(BirthCertificate.objects.all().filter(date_created=))

# print(_(views.actions[0]['title']))

certificate = BirthCertificate.objects.get(pk=5)
# print((certificate.date_register + timedelta(hours=3)).__format__('%d'))
# father = certificate.father
# mother = certificate.mother
# born = certificate.born

# print(
#     BirthCertificate.objects.get(born=BirthCertificate.objects.get(born=20).father).pk 
#     if BirthCertificate.objects.filter(born=BirthCertificate.objects.get(born=20).father)
#     else None
#     if BirthCertificate.objects.filter(born=20) 
#     else None
# )
# print(BirthCertificate.objects.get(born=father).born.birthday.astimezone() if BirthCertificate.objects.filter(born=father) else None)

# from django.utils.translation import ngettext as _n

# count = 1

# print(_n("%(count)d projet", "%(count)d projets", count) % {"count": count})

# for certificate in BirthCertificate.objects.all():
#     print(_n("%(age)d year old", "%(age)d years old", datetime.today().year - certificate.born.birthday.year) % {"age": datetime.today().year - certificate.born.birthday.year})
#     print(certificate)
# filter = BirthCertificate.objects.filter(father=1, mother=mother)
# print(filter.exists())
# print(filter.count())

# print("Kenn Keren ".strip() + "Keren ".strip())


combined = sorted(
    chain(BirthCertificate.objects.all(), DeathCertificate.objects.all()),
    key=attrgetter('date_register'),
    reverse=True
)
print(combined)

# births = BirthCertificate.objects.annotate(cert_type=models.Value('birth', output_field=models.CharField())).values('id', 'date_declaration')
# deaths = DeathCertificate.objects.annotate(cert_type=models.Value('death', output_field=models.CharField())).values('id', 'date_declaration')
# marriages = MarriageCertificate.objects.annotate(cert_type=models.Value('marriage', output_field=models.CharField())).values('id', 'date_declaration')

# print(births.union(births).order_by('date_declaration'))
TIMEZONE_MGA = timezone(timedelta(hours=3))
TIMEZONE_UTC = timezone(timedelta(hours=0))

# date_register = certificate.born.birthday.astimezone(TIMEZONE) + timedelta(days=30)

# print(date_register, datetime.now())
# print((certificate.born.birthday.astimezone(TIMEZONE) + timedelta(days=30)).timestamp() < datetime.now().timestamp())
# print((certificate.born.birthday.astimezone(TIMEZONE) + timedelta(days=30)).timetuple().tm_yday - datetime.now().timetuple().tm_yday)

# print(date_register - timedelta(seconds=))

# def to_seconds(datetime:datetime)->float:
#     year = datetime.year * (365 + 365/4) * 24 * 60 * 60
#     return year

# print(to_seconds(date_register))

# marriages = marriages.annotate(person_name=models.F("husband_name"))
# print(births.union(births, marriages).order_by('date_declaration'))

# Fil d'attende d'enregistrement
""" Chaque Certificat de Naissance doit attendre 30j après la date de naissance 
pour être enregisté. """

# birthday = certificate.born.birthday.astimezone(TIMEZONE)

# print("La date de naissance :", birthday)

# waiting_room = [
#     {
#         'birthday': cert[0],
#         'date_register': None,
#     } for cert in BirthCertificate.objects.filter(
#         born__birthday__year= datetime.today().year,
#     ).values_list('born__birthday')
# ]

# print(waiting_room)

# for index, certificate in enumerate(waiting_room):
#     # Enregistrer un certificat qui a atteint le délai d'attente
#     if datetime.now().timestamp() >= (certificate['birthday'] + timedelta(days=30)).timestamp():
#         print("Le certificat a déjà atteint le délai d'attente.")
#         if not waiting_room[index]['date_register']:
#             print("Le certificat n'est pas encore enregistré")
#             waiting_room[index]['date_register'] = certificate['birthday'] + timedelta(days=30)
#         print("La date d'enregistrement :", waiting_room[index]['date_register'])
#     else:
#         print("Le certificat n'a pas encore atteint le délai d'attente.")

# print(waiting_room)
# 

# fokotany = Fokotany.objects.all()
# births = BirthCertificate.objects.all()
# deaths = DeathCertificate.objects.all()
# marriages = MarriageCertificate.objects.all()

# year_selected = datetime.now().year

# year__first_day = datetime(year_selected, 1, 1, tzinfo=timezone(timedelta(hours=0)))
# year__last_day = datetime(year_selected, 12, 31, tzinfo=timezone(timedelta(hours=0)))

# births_this_year_fkt = {
#     fkt.pk: [births.filter(
#         date_register__gte=year__first_day,
#         date_register__lte=year__last_day,
#         fokotany=fkt
#     ).annotate(gender=models.F('born__gender'))
#     .values('gender').annotate(
#         count=Count('gender')
#     )] for fkt in fokotany
# }

# deaths_this_year_fkt = {
#     fkt.pk: [deaths.filter(
#         date_created__gte=year__first_day,
#         date_created__lte=year__last_day,
#         fokotany=fkt
#     ).annotate(gender=models.F('dead__gender'))
#     .values('gender').annotate(
#         count=Count('gender', distinct=True)
#     )] for fkt in fokotany
# }

# print(births_this_year_fkt)

# formated_gender = {}

# formated_births = {}
# formated_death = {}

# GENDER_CHOICES = {
#         'M': _("Male"),
#         'F': _("Female")
#     }
# for fkt in fokotany:
#     formated_gender[fkt.pk] = []
#     for gender in GENDER_CHOICES:
#         gender_fkt = {
#             'gender': GENDER_CHOICES[gender], 
#             'count': []
#         }
#         for birth in births_this_year_fkt[fkt.pk][0]:
#             if gender == birth['gender']:
#                 print(birth)
#                 gender_fkt['count'].append(birth['count'])
#         for death in deaths_this_year_fkt[fkt.pk][0]:
#             if gender == death['gender']:
#                 print(death)
#                 gender_fkt['count'].append(death['count'])
#         formated_gender[fkt.pk].append(gender_fkt)


# certificates_year = {
#         fkt.name: json.dumps({
#             "labels": ['Acte de Naissance', 'Acte de Décès'],
#             "datasets": [
#                 {
#                     'label': gender['gender'],
#                     'data': gender['count'],
#                     'backgroundColor': "#5697ff",
#                     'borderColor': '#5697ff',
#                     'borderRadius': 50,
#                 } for gender in formated_gender[fkt.pk]
#             ]
#         }) for fkt in fokotany
#     }
# print(certificates_year)

# for fkt in fokotany:
#     formated_births[fkt.pk] = {}
#     formated_death[fkt.pk] = {}
#     for birth in births_this_year_fkt[fkt.pk]:
#         formated_births[fkt.pk]["gender"] = [
#             GENDER_CHOICES[gender['gender']] for gender in birth
#         ]
#         formated_births[fkt.pk]["count"] = [
#             float(gender['count']) for gender in birth
#         ]
#     for death in deaths_this_year_fkt[fkt.pk]:
#         formated_death[fkt.pk]["gender"] = [
#             GENDER_CHOICES[gender['gender']] for gender in death
#         ]
#         formated_death[fkt.pk]["count"] = [
#             float(gender['count']) for gender in death
#         ]

# certificates_year = [
#     json.dumps({
#         "labels": ['Acte de Naissance', 'Acte de Décès'],
#         "datasets": [
#             {
#                 'label': formated_births[fkt.pk]['gender'],
#                 'data': formated_births[fkt.pk]['count'],
#                 'backgroundColor': "#5697ff",
#                 'borderColor': '#5697ff',
#                 'borderRadius': 50,
#             },
#             {
#                 'label': formated_death[fkt.pk]['gender'],
#                 'data': formated_death[fkt.pk]['count'],
#                 'backgroundColor': '#6b7280',
#                 'borderColor': '#6b7280',
#                 'borderRadius': 50,
#             },
#         ]
#     }) for fkt in fokotany
# ]

# print(certificates_year)

# birth_dict = {birth['gender']: birth['count'] for birth in births_this_year_fkt}
# death_dict = {death['gender']: death['count'] for death in deaths_this_year_fkt}

# all_months = sorted(set(birth_dict.keys()) | set(death_dict.keys()))

# print(birth_dict)
# print(death_dict)
# print(all_months)

# formatted_births = []
# formatted_deaths = []

# context = {}

# for mois_str in all_months:
#     birth_mois = birth_dict.get(mois_str, Decimal('0'))
#     death_mois = death_dict.get(mois_str, Decimal('0'))
    
#     # Convertir la chaîne de date en objet datetime pour le formatage
#     mois_date = datetime.strptime(mois_str, '%Y-%m')

#     formatted_births.append({
#         'mois': {"year": mois_date.year, "month": mois_date.month},
#         'total': float(birth_mois)  # Convertir en float pour JSON
#     })
#     formatted_deaths.append({
#         'mois':  {"year": mois_date.year, "month": mois_date.month},
#         'total': float(death_mois)  # Convertir en float pour JSON
#     })

# print(formatted_births)
# print(formatted_deaths)

# context['formatted_births'] = json.dumps(formatted_births[::-1])
# context['formatted_deaths'] = json.dumps(formatted_deaths[::-1])


# print(context)


# activate('en')

# print(EXEMPLE % {'example': 'Kenn'})