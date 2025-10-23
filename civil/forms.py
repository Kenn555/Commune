from datetime import date, datetime, timedelta
from django import forms
from django.utils.translation import gettext_lazy as _
from dal import autocomplete

from administration.models import Common, Fokotany, Role, Service
from civil.models import BirthCertificate, DeathCertificate, Person


CLASS_FIELD = """
        w-full bg-transparent border-0 border-b-2 border-b-gray-300
        outline-none font-medium text-base tracking-wider
        focus:outline-none focus:border-b-blue-400
        focus:ring-0 focus:ring-offset-0
    """


class BirthCertificateForm(forms.Form):
    # Matricule
    fokotany = forms.ChoiceField(
        label=_("Fokotany"), 
        choices=Fokotany.objects.values_list("id","name").order_by('name'),
        initial=Fokotany.objects.get(name=Common.objects.get(pk=1).name.capitalize()).pk,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD + "text-lg cursor-pointer", 
                "placeholder": "e.g. Betsiaka",
                "title": "Fokotany",
            }
        )
    )
    
    number = forms.CharField(
        label=_("Number"), 
        disabled=True,
        # initial="1".zfill(9) if not BirthCertificate.objects.count() else str(BirthCertificate.objects.last().id + 1).zfill(9),
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD.replace("w-full min-w-52", "w-36 text-gray-500") + " text-center text-lg tracking-widest cursor-pointer", 
                "placeholder": "0000000001",
                "title": "Matricule",
            }
        )
    )
    
    # Informations personnelles
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his last name"),
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    first_name = forms.CharField(
        label=_("First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his first name"),
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    gender = forms.ChoiceField(
        label=_("Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender")
            }
        )
    )
    
    birth_place = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert the place of birth"),
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    birthday = forms.DateTimeField(
        label=_("Birthday"), 
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Enter/Choose the date of birth")
            }
        )
    )

    is_alive = forms.BooleanField(
        label=_("Alive"),
        required=False,
        initial=True,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    # Informations sur les parents avec autocomplete
    use_existing_father = forms.BooleanField(
        label=_("Search for a existing Mother"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    existing_father = forms.ModelChoiceField(
        label=_("Existing Father"),
        queryset=Person.objects.filter(gender='M', birthday__lte=date.today() - timedelta(days=18*365)),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='civil:father-autocomplete',
            attrs={
                "class": CLASS_FIELD,
                "data-placeholder": _("Search for Father..."),
                "data-minimum-input-length": 2,
            }
        )
    )
    
    father_name = forms.CharField(
        label=_("Father's Full Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for her/his father's full name"),
                "title": _("Wait for her/his father's full name"),
            }
        )
    )
    
    father_place_of_birth = forms.CharField(
        label=_("Place of Birth"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for her/his father's place of birth"),
                "title": _("Wait for her/his father's place of birth"),
            }
        )
    )
    
    father_birthday = forms.DateTimeField(
        label=_("Birthday"), 
        required=False,
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for her/his father's date of birth")
            }
        )
    )
    
    father_job = forms.CharField(
        label=_("Father's Job"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his father's job"),
                "title": _("Insert her/his father's job"),
            }
        )
    )

    father_address = forms.CharField(
        label=_("Father's Address"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his father's address"),
                "title": _("Insert her/his father's address"),
            }
        )
    )

    # Mère
    use_existing_mother = forms.BooleanField(
        label=_("Search for a existing Mother"),
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    existing_mother = forms.ModelChoiceField(
        label=_("Existing Mother"),
        queryset=Person.objects.filter(gender='F', birthday__lte=date.today() - timedelta(days=18*365)),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='civil:mother-autocomplete',
            attrs={
                "class": CLASS_FIELD,
                "data-placeholder": _("Search for Mother..."),
                "data-minimum-input-length": 2,
            }
        )
    )
    
    mother_name = forms.CharField(
        label=_("Mother's Full Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for her/his mother's full name"),
                "title": _("Wait for her/his mother's full name"),
            }
        )
    )
    
    mother_place_of_birth = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for her/his mother's place of birth"),
                "title": _("Wait for her/his mother's place of birth"),
            }
        )
    )
    
    mother_birthday = forms.DateTimeField(
        label=_("Birthday"), 
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for her/his mother's date of birth")
            }
        )
    )
    
    mother_job = forms.CharField(
        label=_("Mother's Job"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his mother's job"),
                "title": _("Insert her/his mother's job"),
            }
        )
    )
    
    mother_address = forms.CharField(
        label=_("Mother's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his mother's address"),
                "title": _("Insert her/his mother's address"),
            }
        )
    )

    # Déclarant    
    existing_declarer = forms.ModelChoiceField(
        label=_("Existing Declarer"),
        queryset=Person.objects.filter(birthday__lte=date.today() - timedelta(days=18*365)),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='civil:person-autocomplete',
            attrs={
                "class": CLASS_FIELD,
                "data-placeholder": _("Search for Declarer..."),
                "data-minimum-input-length": 2,
            }
        )
    )
    
    declarer_name = forms.CharField(
        label=_("Declarer's Full Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for the declarer's full name"),
                "title": _("Wait for the declarer's full name"),
            }
        )
    )
    
    declarer_place_of_birth = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for the declarer's place of birth"),
                "title": _("Wait for the declarer's place of birth"),
            }
        )
    )
    
    declarer_birthday = forms.DateTimeField(
        label=_("Birthday"), 
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for the declarer's date of birth")
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert the declarer's job"),
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert the declarer's address"),
                "title": _("Insert the declarer's address"),
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["fokotany", "number"],
        _("Informations"): ["last_name", "first_name", "gender", "birth_place", "birthday", "is_alive"],
        _("Other Informations"): {
            _("father"): [
                "use_existing_father", "existing_father",
                "father_name", "father_place_of_birth", "father_birthday", "father_job", "father_address"
            ],
            _("mother"): ["use_existing_mother", "existing_mother",
                "mother_name", "mother_place_of_birth", "mother_birthday", "mother_job", "mother_address"
            ],
            _("declarer"): ["existing_declarer", "declarer_name", "declarer_place_of_birth", "declarer_birthday", "declarer_job", "declarer_address"]
        },
    }

    @property
    def fieldsets_fields(self):
        fs = {}
        for title, fields in self.fieldsets.items():
            # Cas 1 : la section est une simple liste de champs
            if isinstance(fields, (list, tuple)):
                fs[title] = [self[ch] for ch in fields]

            # Cas 2 : la section contient des sous-groupes (dictionnaire imbriqué)
            elif isinstance(fields, dict):
                sub_fs = {}
                for sub_title, sub_fields in fields.items():
                    sub_fs[sub_title] = [self[ch] for ch in sub_fields]
                fs[title] = sub_fs

            # Cas 3 : si un autre type apparaît (sécurité)
            else:
                raise TypeError(f"Invalid type for fieldset '{title}': {type(fields).__name__}")

        return fs



class DeathCertificateForm(forms.Form):
    # Matricule
    fokotany = forms.ChoiceField(
        label=_("Fokotany"), 
        choices=Fokotany.objects.values_list("id","name").order_by('name'),
        initial=Fokotany.objects.get(name=Common.objects.get(pk=1).name.capitalize()).pk,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD + "text-lg cursor-pointer", 
                "placeholder": "e.g. Betsiaka",
                "title": "Fokotany",
            }
        )
    )
    
    number = forms.CharField(
        label=_("Number"), 
        disabled=True,
        initial="1".zfill(9) if not DeathCertificate.objects.count() else str(DeathCertificate.objects.last().id + 1).zfill(9),
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD.replace("w-full min-w-52", "w-36 text-gray-500") + " text-center text-lg tracking-widest cursor-pointer", 
                "placeholder": "0000000001",
                "title": "Matricule",
            }
        )
    )
    
    
    # Informations personnelles
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + ' searched_person', 
                "placeholder": _("Insert her/his last name"),
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    first_name = forms.CharField(
        label=_("First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his first name"),
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    gender = forms.ChoiceField(
        label=_("Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender")
            }
        )
    )
    
    birth_place = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert the place of birth"),
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    birthday = forms.DateTimeField(
        label=_("Birthday"), 
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Enter/Choose the date of birth")
            }
        )
    )

    # Déclarant    
    existing_declarer = forms.ModelChoiceField(
        label=_("Existing Declarer"),
        queryset=Person.objects.filter(birthday__lte=date.today() - timedelta(days=18*365)),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='civil:person-autocomplete',
            attrs={
                "class": CLASS_FIELD,
                "data-placeholder": _("Search for Declarer..."),
                "data-minimum-input-length": 2,
            }
        )
    )
    
    declarer_name = forms.CharField(
        label=_("Declarer's Full Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for the declarer's full name"),
                "title": _("Wait for the declarer's full name"),
            }
        )
    )
    
    declarer_place_of_birth = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Wait for the declarer's place of birth"),
                "title": _("Wait for the declarer's place of birth"),
            }
        )
    )
    
    declarer_birthday = forms.DateTimeField(
        label=_("Birthday"), 
        # initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for the declarer's date of birth")
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert the declarer's job"),
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + ' searched_person', 
                "placeholder": _("Insert the declarer's address"),
                "title": _("Insert the declarer's address"),
            }
        )
    )
    
    

    fieldsets = {
        _("Matricule"): ["fokotany", "number"],
        _("Informations"): ["last_name", "first_name", "gender", "birth_place", "birthday"],
        _("Other Informations"): {
            _("declarer"): ["existing_declarer", "declarer_name", "declarer_place_of_birth", "declarer_birthday", "declarer_job", "declarer_address"]
        },
    }

    @property
    def fieldsets_fields(self):
        fs = {}
        for title, fields in self.fieldsets.items():
            # Cas 1 : la section est une simple liste de champs
            if isinstance(fields, (list, tuple)):
                fs[title] = [self[ch] for ch in fields]

            # Cas 2 : la section contient des sous-groupes (dictionnaire imbriqué)
            elif isinstance(fields, dict):
                sub_fs = {}
                for sub_title, sub_fields in fields.items():
                    sub_fs[sub_title] = [self[ch] for ch in sub_fields]
                fs[title] = sub_fs

            # Cas 3 : si un autre type apparaît (sécurité)
            else:
                raise TypeError(f"Invalid type for fieldset '{title}': {type(fields).__name__}")

        return fs


class MarriageCertificateForm(forms.Form):
    last_name_man = forms.CharField(
        label=_("Last Name"), 
        initial=_("Insert her/his last name")
    )
    
    first_name_man = forms.CharField(
        label=_("First Name")
    )
    
    date_of_marriage = forms.DateField(
        label=_("Date of Marriage"), 
        widget=forms.SelectDateWidget(years=range(1900, 2026))
    )
    
    place_of_marriage = forms.CharField(
        label=_("Place of Marriage")
    )