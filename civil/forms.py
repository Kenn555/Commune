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
                "title": "Fokotany",
            }
        )
    )
    
    # Informations personnelles
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    first_name = forms.CharField(
        label=_("First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
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
    father_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    father_last_name = forms.CharField(
        label=_("Father's Last Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "M",
                "title": _("Wait for her/his father's full name"),
            }
        )
    )
    
    father_first_name = forms.CharField(
        label=_("Father's First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "M",
                "title": _("Wait for her/his father's full name"),
            }
        )
    )
    
    father_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
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
                "title": _("Insert her/his father's address"),
            }
        )
    )

    # Mère
    mother_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    mother_last_name = forms.CharField(
        label=_("Mother's Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "F",
                "title": _("Wait for her/his mother's full name"),
            }
        )
    )
    
    mother_first_name = forms.CharField(
        label=_("Mother's First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "F",
                "title": _("Wait for her/his mother's full name"),
            }
        )
    )
    
    mother_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
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
                "title": _("Insert her/his mother's job"),
            }
        )
    )
    
    mother_address = forms.CharField(
        label=_("Mother's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his mother's address"),
            }
        )
    )

    # Déclarant  
    declarer_present = forms.BooleanField(
        label=_("Was Present"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    declarer_last_name = forms.CharField(
        label=_("Declarer's Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "title": _("Wait for the declarer's full name"),
            }
        )
    )
    
    declarer_first_name = forms.CharField(
        label=_("Declarer's First Name"),
        required=False, 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "title": _("Wait for the declarer's full name"),
            }
        )
    )
    
    declarer_gender = forms.ChoiceField(
        label=_("Declarer's Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender of declarer")
            }
        )
    )
    
    declarer_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
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
    
    declarer_relation = forms.CharField(
        label=_("Relationship"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the relationship with declarer"),
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's address"),
            }
        )
    )
    
    declaration_date = forms.DateTimeField(
        label=_("Date of Declaration"),     
        initial=(datetime.now() - timedelta(days=30)).__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for the date of declaration")
            }
        )
    )
    
    register_date = forms.DateTimeField(
        label=_("Date of Register"), 
        initial=datetime.now().__format__("%Y-%m-%d %H:%M"),
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for the date of register")
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["fokotany"],
        _("Informations"): ["last_name", "first_name", "gender", "birth_place", "birthday", "is_alive"],
        _("Other Informations"): {
            _("father"): [
                "father_exist", "father_last_name",
                "father_first_name", "father_birth_place", "father_birthday", "father_job", "father_address"
            ],
            _("mother"): ["mother_exist", "mother_last_name",
                "mother_first_name", "mother_birth_place", "mother_birthday", "mother_job", "mother_address"
            ],
            _("declarer"): ["declarer_present", "declarer_last_name", "declarer_first_name", "declarer_gender", "declarer_birth_place", "declarer_birthday", "declarer_relation", "declarer_job", "declarer_address", "declaration_date", "register_date"]
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
                "title": "Fokotany",
            }
        )
    )
    
    # Informations personnelles
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + ' searched_person', 
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    first_name = forms.CharField(
        label=_("First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
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
    
    death_place = forms.CharField(
        label=_("Place of Death"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    death_day = forms.DateTimeField(
        label=_("Day of Death"), 
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
    
    dead_job = forms.CharField(
        label=_("Job"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the dead's job"),
            }
        )
    )
    
    dead_address = forms.CharField(
        label=_("Address"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the dead's address"),
            }
        )
    )

    # Informations sur les parents avec autocomplete
    father_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    father_last_name = forms.CharField(
        label=_("Father's Last Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "M",
                "title": _("Wait for her/his father's last name"),
            }
        )
    )

    father_first_name = forms.CharField(
        label=_("Father's first Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "    M",
                "title": _("Wait for her/his father's first name"),
            }
        )
    )

    father_was_alive = forms.BooleanField(
        label=_("He is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    # Mère
    mother_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )
    
    mother_last_name = forms.CharField(
        label=_("Mother's Last Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "F",
                "title": _("Wait for her/his mother's last name"),
            }
        )
    )
    
    mother_first_name = forms.CharField(
        label=_("Mother's First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "F",
                "title": _("Wait for her/his mother's first name"),
            }
        )
    )

    mother_was_alive = forms.BooleanField(
        label=_("She is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    # Déclareur
    declarer_present = forms.BooleanField(
        label=_("Was Present"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    declarer_last_name = forms.CharField(
        label=_("Declarer's Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "title": _("Wait for the declarer's last name"),
            }
        )
    )
    
    declarer_first_name = forms.CharField(
        label=_("Declarer's First Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "title": _("Wait for the declarer's first name"),
            }
        )
    )
    
    declarer_gender = forms.ChoiceField(
        label=_("Declarer's Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender of declarer")
            }
        )
    )
    
    declarer_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
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
    
    declaration_date = forms.DateTimeField(
        label=_("Date of Declaration"), 
        initial=datetime.now().__format__("%Y-%m-%d %H:%M"), 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Wait for the date of declaration")
            }
        )
    )
    
    declarer_relation = forms.CharField(
        label=_("Relationship"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the relationship with declarer"),
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's address"),
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["fokotany"],
        _("Informations"): ["last_name", "first_name", "gender", "birth_place", "birthday", "death_place", "death_day", "dead_job", "dead_address"],
        _("Other Informations"): {
            _("father"): [ "father_exist", "father_last_name", "father_first_name", "father_was_alive"],
            _("mother"): ["mother_exist", "mother_last_name","mother_first_name", "mother_was_alive"],
            _("declarer"): ["declarer_present", "declarer_last_name", "declarer_first_name", "declarer_gender", "declarer_birth_place", "declarer_birthday", "declarer_relation", "declarer_job", "declarer_address", "declaration_date"]
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