from django.test import TestCase

from administration.models import Fokotany, Sector
from civil.models import BirthCertificate

# Create your tests here.

FOKOTANY_SECTOR = {
"Ankatoko": [f"Secteur {i}" for i in range(1, 6)],
"Betsiaka": [f"Secteur {i}" for i in range(1, 6)],
"Andrafialava": [f"Secteur {i}" for i in range(1, 6)],
"Ankaramy": [f"Secteur {i}" for i in range(1, 6)],
"Antanamivony": [f"Secteur {i}" for i in range(1, 6)],
"Ankararata Loky": [f"Secteur {i}" for i in range(1, 6)],
"Fihety": [f"Secteur {i}" for i in range(1, 6)],
"Mosorobe": [f"Secteur {i}" for i in range(1, 6)],
"Sandragnary": [f"Secteur {i}" for i in range(1, 6)],
"Ampahaka": [f"Secteur {i}" for i in range(1, 6)],
"Tanambao Mangihy": [f"Secteur {i}" for i in range(1, 6)],
"Morafeno": [f"Secteur {i}" for i in range(1, 6)],
}

def initial_values():
    for fokotany in FOKOTANY_SECTOR.keys():
        fkt = Fokotany.objects.create(name = fokotany)
        for sector in FOKOTANY_SECTOR[fokotany]:
            Sector.objects.create(
                name = sector,
                fokotany = fkt
            )

# ftk = Fokotany.objects.values_list("id","name")

# print(ftk)

print(BirthCertificate.objects.last().mother)