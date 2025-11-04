from django import template
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    return json.dumps({
        'id': value.id,
        'username': value.username,
        'email': value.email,
        'first_name': value.first_name,
        'last_name': value.last_name,
        'is_staff': value.is_staff,
        'is_active': value.is_active
    }, cls=DjangoJSONEncoder)


class IsaGasy:
    """  """
    def __init__(self, isa: int):
        self.isa = isa
        # Isa Malagasy 
        self.__isa_boky = [
            ["iraiky", "roa", "telo", "efatra", "dimy", "enina", "fito", "valo", "sivy"],
            ["folo","roapolo","telopolo","efapolo","dimampolo","enimpolo","fitopolo","valopolo","sivifolo",],
            ["zato","roanjato","telonjato","efajato","dimanjato","eninjato","fitonjato","valonjato","sivanjato",],
        ]
        self.__isa_boky.append(["arivo"] + [i + " arivo" for i in self.__isa_boky[0][1:]])
        isa_lavitra = [
            "alina",
            "hetsy",
            "tampitrisa",
            "safatsiroa",
            "tsitamboisa",
            "lavitrisa",
            "alinkisa",
            "tsipesimpesenina",
            "tsikofotsiforohana",
            "tsihitanoanoa",
        ]
        d = 0
        j = 0
        for n in range(0, 100):
            isa_tambatra = ""
            if n < 96:
                if n < len(isa_lavitra) :
                    isa_tambatra = isa_lavitra[n]
                else :
                    if j%len(isa_lavitra) == 0:
                        d += 1
                        j += 3 

                    if d < 9:
                        isa_tambatra = isa_lavitra[j%len(isa_lavitra)] + "faha" + self.__isa_boky[0][d]
                    elif d == 9:
                        isa_tambatra = isa_lavitra[j%len(isa_lavitra)] + "faha" + self.__isa_boky[1][0]
                    else:           
                        isa_tambatra = isa_lavitra[j%len(isa_lavitra)] + "faha" + self.__isa_boky[0][d%len(self.__isa_boky[0])-1] + "ambini" + self.__isa_boky[1][0]
                    j += 1
            elif n == 96:
                isa_tambatra = "gogola"
            else:
                break

            self.__isa_boky.append([])
            for p in self.__isa_boky[0]:
                self.__isa_boky[-1].append(p + " " + isa_tambatra)

    def ho_teny(self) -> str :
        """ Traduit un nombre (jusqu'à 101 chiffres) en Isa Malagasy """
        resultat = ""
        nombre_str = ""

        for c in str(self.isa):
            nombre_str = c + nombre_str

        if nombre_str == "1":
            resultat = 'iray'
        else:
            for index, isa in enumerate(nombre_str):  
                if isa != "0":
                    if index != 0 and int(nombre_str[:index]) != 0:
                        if index in range(1, len(self.__isa_boky)):
                            if index == 1 and isa == "1":
                                resultat += " ambin'ny "
                            # elif (self.__isa_boky[index][int(isa)-1] in self.__isa_boky + [self.__isa_boky[0]]):
                            elif index == 1:
                                resultat += " amby "
                            else:
                                resultat += " sy "

                    resultat += self.__isa_boky[index][int(isa)-1]

        return resultat    

    def zarateny(self, teny: str, mihisa: int)->list[str]:
        valiny = []
        laharana = -1
        for faha in range(len(teny)):
            if faha % mihisa == 0:
                valiny.append(teny[faha])
                laharana += 1
            else:
                valiny[laharana] += teny[faha]
        return valiny
    

class VolanaGasy():
    def __init__(self, volana:int):
        self.volana = volana
        # Isa Malagasy 
        self.__volana_boky = [
            "janoary",
            "febroary",
            "martsa",
            "aprily",
            "mey",
            "jona",
            "jolay",
            "aogostra",
            "septambra",
            "octobra",
            "novambra",
            "desambra",
        ]

    def ho_teny(self) -> str:
        return self.__volana_boky[self.volana - 1]


class OraGasy():
    def __init__(self, ora:int):
        self.ora = ora.__mod__(24)
        # Isa Malagasy 
        self.__ora_boky = [
            "maraina",
            "atoandro",
            "tolak'andro",
            "hariva",
            "alina",
        ]

    def ho_teny(self) -> str:
        if 3 <= self.ora < 11:
            sokajy = self.__ora_boky[0]
        elif 11 <= self.ora < 14:
            sokajy = self.__ora_boky[1]
        elif 14 <= self.ora < 17:
            sokajy = self.__ora_boky[2]
        elif 17 <= self.ora < 20:
            sokajy = self.__ora_boky[3]
        else:
            sokajy = self.__ora_boky[4]
        
        return sokajy
        ...

# Custom filter to format numbers with space separator
@register.filter
def isa_gasy(value) -> str:
    try:
        value = int(value)
        return IsaGasy(value).ho_teny()
    except (ValueError, TypeError):
        return value
    
@register.filter
def volana_gasy(value) -> str:
    try:
        value = int(value)
        return VolanaGasy(value).ho_teny()
    except (ValueError, TypeError):
        return value
    
@register.filter
def ora_gasy(value) -> str:
    try:
        value = int(value)
        return OraGasy(value).ho_teny()
    except (ValueError, TypeError):
        return value