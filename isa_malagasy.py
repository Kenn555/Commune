class IsaGasy:
    """  """
    def __init__(self, isa: int):
        self.isa = isa
        # Isa Malagasy 
        self.__isa_boky = [
            ["iray", "roa", "telo", "efatra", "dimy", "enina", "fito", "valo", "sivy"],
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

        for index, isa in enumerate(nombre_str):  
            if isa != "0":
                if index == 0 and int(nombre_str[index]) == 1 and int(nombre_str[1]) != 0:
                    resultat += 'iraiky'
                    continue
                if index != 0 and int(nombre_str[:index]) != 0:
                    if index in range(1, len(self.__isa_boky)):
                        if index == 1 and isa == "1":
                            resultat += " ambin'ny "
                        # elif (self.__isa_boky[index][int(isa)-1] in self.__isa_boky + [self.__isa_boky[0]]):
                        elif index == 1 or (index == 2 and int(nombre_str[index]) == 1):
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
    
print(IsaGasy(299).ho_teny())