from datetime import datetime
from django.db.utils import IntegrityError
from django.test import TestCase

from administration.models import Fokotany
from civil import views
from civil.models import Person, BirthCertificate
from django.utils.translation import activate
from django.utils.translation import gettext as _

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

table = {
            "headers": ["Nom", "Prénom", "Genre", "Âge"], 
            "rows": [
                {
                    "index" : index,
                    "row": [
                        {"last_name": birth.born.last_name, "style": ""},
                        {"first_name": birth.born.first_name, "style": ""},
                        {"gender": Person.GENDER_CHOICES[birth.born.gender], "style": ""},
                        {"age": datetime.today().year - birth.born.birthday.year, "style": ""},
                    ],
                } for index, birth in enumerate(BirthCertificate.objects.all())
            ],
        }

# for row in table['rows']:
#     print(row['index'], row['row'])


activate('mg')

print(_(views.actions[0]['title']))

from django.utils.translation import ngettext as _n

count = 2

print(_n("%(count)d projet", "%(count)d projets", count) % {"count": count})

for certificate in BirthCertificate.objects.all():
    print(_n("%(age)d year old", "%(age)d years old", datetime.today().year - certificate.born.birthday.year) % {"age": datetime.today().year - certificate.born.birthday.year})
    print(certificate)