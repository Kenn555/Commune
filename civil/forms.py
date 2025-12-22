from datetime import date, datetime, timedelta
from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Concat
from django.db import models

from administration.models import Common, Fokotany, Role, Service, Staff
from civil.models import BirthCertificate, DeathCertificate, Person


CLASS_FIELD = """
        w-full bg-transparent border-0 border-b-2 border-b-gray-300
        outline-none font-medium text-base tracking-wider
        focus:outline-none focus:border-b-[#007e3a]
        focus:ring-0 focus:ring-offset-0
    """

class PersonForm(forms.Form):    
    # Informations personnelles
    last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
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
        strip=True,
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
        strip=True,
        required=False,
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
        required=False, 
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "max": datetime.now().__format__("%Y-%m-%d %H:%M"),
                "title": _("Enter/Choose the date of birth")
            }
        )
    )
    
    job = forms.CharField(
        label=_("Job"),
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the person's job"),
            }
        )
    )
    
    address = forms.CharField(
        label=_("Address"),
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the person's address"),
            }
        )
    )

    is_alive = forms.BooleanField(
        label=_("Alive"),
        required=False,
        initial=True,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    fieldsets = {
        _("Informations"): ["birthday", "birth_place", "last_name", "first_name", "gender", "job", "address", "is_alive"],
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
        strip=True,
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
        strip=True,
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
        strip=True,
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
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Informations sur les parents avec autocomplete
    father_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )
    
    father_last_name = forms.CharField(
        label=_("Father's Last Name"), 
        strip=True,
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
        strip=True,
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
        strip=True,
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
        strip=True,
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
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his father's address"),
            }
        )
    )

    father_was_alive = forms.BooleanField(
        label=_("He is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Mère
    mother_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )
    
    mother_last_name = forms.CharField(
        label=_("Mother's Last Name"), 
        strip=True,
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
        strip=True,
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
        strip=True,
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
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his mother's job"),
            }
        )
    )
    
    mother_address = forms.CharField(
        label=_("Mother's Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his mother's address"),
            }
        )
    )

    mother_was_alive = forms.BooleanField(
        label=_("She is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Déclarant  
    declarer_present = forms.BooleanField(
        label=_("Was Present"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    declarer_last_name = forms.CharField(
        label=_("Declarer's Last Name"), 
        strip=True,
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
        strip=True,
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
        strip=True,
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
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the relationship with declarer"),
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        strip=True,
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

    # Responsable
    staff_direction = []
    for staff in Staff.objects.filter(role__service__grade=1).order_by('role__grade'):
        staff_direction.append((staff.pk, staff.full_name + ', ' + staff.role.title))
    responsible = forms.ChoiceField(
        label=_("Responsible"), 
        choices = staff_direction,
        initial = staff_direction[0],
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD + "cursor-pointer", 
                "title": "Responsible",
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["fokotany"],
        _("Informations"): ["birthday", "birth_place", "last_name", "first_name", "gender", "is_alive"],
        _("Parent Informations"): {
            _("father"): [
                "father_exist", "father_last_name",
                "father_first_name", "father_birthday", "father_birth_place", "father_job", "father_address", "father_was_alive"
            ],
            _("mother"): ["mother_exist", "mother_last_name",
                "mother_first_name", "mother_birthday", "mother_birth_place", "mother_job", "mother_address", "mother_was_alive"
            ],
            _("declarer"): ["declarer_present", "declarer_last_name", "declarer_first_name", "declarer_gender", "declarer_birthday", "declarer_birth_place", "declarer_job", "declarer_address", "declarer_relation",],
        },
        _("Register Informations"): {
            _("register"): ["responsible", "declaration_date", "register_date"],
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
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + ' searched_person', 
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
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
        strip=True,
        required=False, 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    birthday = forms.DateTimeField(
        label=_("Birthday"), 
        required=False,
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
        strip=True,
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
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the person's job"),
            }
        )
    )
    
    dead_address = forms.CharField(
        label=_("Address"),
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the person's address"),
            }
        )
    )

    # Informations sur les parents avec autocomplete
    father_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )
    
    father_last_name = forms.CharField(
        label=_("Father's Last Name"), 
        strip=True,
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
        strip=True,
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
    
    father_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
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
        strip=True,
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
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his father's address"),
            }
        )
    )

    father_was_alive = forms.BooleanField(
        label=_("He is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Mère
    mother_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )
    
    mother_last_name = forms.CharField(
        label=_("Mother's Last Name"), 
        strip=True,
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
        strip=True,
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
    
    mother_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for her/his mother's place of birth"),
            }
        )
    )
    
    mother_birthday = forms.DateTimeField(
        label=_("Birthday"), 
        required=False,
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
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his mother's job"),
            }
        )
    )
    
    mother_address = forms.CharField(
        label=_("Mother's Address"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his mother's address"),
            }
        )
    )

    mother_was_alive = forms.BooleanField(
        label=_("She is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Déclareur
    declarer_present = forms.BooleanField(
        label=_("Was Present"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    declarer_last_name = forms.CharField(
        label=_("Declarer's Last Name"), 
        strip=True,
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
        strip=True,
        required=False,
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
        strip=True,
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
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the relationship with declarer"),
            }
        )
    )
    
    declarer_job = forms.CharField(
        label=_("Declarer's Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    declarer_address = forms.CharField(
        label=_("Declarer's Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's address"),
            }
        )
    )

    # Responsable
    staff_direction = []
    for staff in Staff.objects.filter(role__service__grade=1).order_by('role__grade'):
        staff_direction.append((staff.pk, staff.full_name + ', ' + staff.role.title))
    responsible = forms.ChoiceField(
        label=_("Responsible"), 
        choices = staff_direction,
        initial = staff_direction[0],
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD + "cursor-pointer", 
                "title": "Responsible",
            }
        )
    )

    # Enregistrement
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
        _("Informations"): ["death_day", "death_place", "last_name", "first_name", "gender", "birthday", "birth_place", "dead_job", "dead_address"],
        _("Parent Informations"): {
            _("father"): [ "father_exist", "father_last_name", "father_first_name", "father_birthday", "father_birth_place", "father_job", "father_address", "father_was_alive"],
            _("mother"): ["mother_exist", "mother_last_name","mother_first_name", "mother_birthday", "mother_birth_place", "mother_job", "mother_address", "mother_was_alive"],
            _("declarer"): ["declarer_present", "declarer_last_name", "declarer_first_name", "declarer_gender", "declarer_birthday", "declarer_birth_place", "declarer_job", "declarer_address", "declarer_relation",],
        },
        _("Register Informations"): {
            _("register"): ["responsible", "declaration_date", "register_date"],
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
    
    # Informations personnelles du marié
    groom_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "M",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    groom_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "M",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    groom_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    groom_birthday = forms.DateTimeField(
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
    
    groom_job = forms.CharField(
        label=_("Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    groom_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )
    
    groom_nationality = forms.CharField(
        label=_("Nationality"), 
        strip=True,
        initial="Malagasy",
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the nationality"),
            }
        )
    )
    
    # Informations des parents du marié
    # Père du marié
    father_groom_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    father_groom_pk = forms.IntegerField(
        show_hidden_initial=False,
        localize=False,
        required=False,
        widget=forms.HiddenInput()
    )

    father_groom_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "M",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    father_groom_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "M",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    father_groom_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )

    father_groom_was_alive = forms.BooleanField(
        label=_("He is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Mère du marié
    mother_groom_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=True,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    mother_groom_pk = forms.IntegerField(
        show_hidden_initial=False,
        localize=False,
        required=False,
        widget=forms.HiddenInput()
    )

    mother_groom_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "F",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    mother_groom_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "F",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    mother_groom_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )

    mother_groom_was_alive = forms.BooleanField(
        label=_("She is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )
    
    # Informations personnelles de la mariée
    bride_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "F",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    bride_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "F",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    bride_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    bride_birthday = forms.DateTimeField(
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
    
    bride_job = forms.CharField(
        label=_("Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the place of birth"),
            }
        )
    )
    
    bride_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )
    
    bride_nationality = forms.CharField(
        label=_("Nationality"), 
        strip=True,
        initial="Malagasy",
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the nationality"),
            }
        )
    )
    
    # Informations des parents de la mariée
    # Père de la mariée
    father_bride_exist = forms.BooleanField(
        label=_("Have a Father"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    father_bride_pk = forms.IntegerField(
        show_hidden_initial=False,
        localize=False,
        required=False,
        widget=forms.HiddenInput()
    )

    father_bride_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "M",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    father_bride_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "M",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    father_bride_job = forms.CharField(
        label=_("Job"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the job"),
            }
        )
    )
    
    father_bride_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )

    father_bride_was_alive = forms.BooleanField(
        label=_("He is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Mère de la mariée
    mother_bride_exist = forms.BooleanField(
        label=_("Have a Mother"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    mother_bride_pk = forms.IntegerField(
        show_hidden_initial=False,
        localize=False,
        required=False,
        widget=forms.HiddenInput()
    )

    mother_bride_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "data-gender": "F",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    mother_bride_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "first_name",
                "data-gender": "F",
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    mother_bride_job = forms.CharField(
        label=_("Job"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the job"),
            }
        )
    )
    
    mother_bride_address = forms.CharField(
        label=_("Address"), 
        strip=True,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the address"),
            }
        )
    )

    mother_bride_was_alive = forms.BooleanField(
        label=_("She is alive"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "mr-2 accent-[#007e3a]"})
    )

    # Informations sur les témoins
    # Témoin du marié
    witness_groom_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    witness_groom_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
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
    
    witness_groom_gender = forms.ChoiceField(
        label=_("Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender")
            }
        )
    )
    
    witness_groom_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the declarer's place of birth"),
            }
        )
    )
    
    witness_groom_birthday = forms.DateTimeField(
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
    
    witness_groom_job = forms.CharField(
        label=_("Declarer's Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    witness_groom_address = forms.CharField(
        label=_("Declarer's Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's address"),
            }
        )
    )

    # Témoin de la mariée
    witness_bride_last_name = forms.CharField(
        label=_("Last Name"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_person", 
                "type": "search",
                "data-type": "last_name",
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    witness_bride_first_name = forms.CharField(
        label=_("First Name"), 
        strip=True,
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
    
    witness_bride_gender = forms.ChoiceField(
        label=_("Gender"), 
        choices=Person.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender")
            }
        )
    )
    
    witness_bride_birth_place = forms.CharField(
        label=_("Place of Birth"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Wait for the declarer's place of birth"),
            }
        )
    )
    
    witness_bride_birthday = forms.DateTimeField(
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
    
    witness_bride_job = forms.CharField(
        label=_("Declarer's Job"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's job"),
            }
        )
    )
    
    witness_bride_address = forms.CharField(
        label=_("Declarer's Address"), 
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert the declarer's address"),
            }
        )
    )

    # Responsable
    staff_direction = []
    for staff in Staff.objects.filter(role__service__grade=1).order_by('role__grade'):
        staff_direction.append((staff.pk, staff.full_name + ', ' + staff.role.title))
    responsible = forms.ChoiceField(
        label=_("Responsible"), 
        choices = staff_direction,
        initial = staff_direction[0],
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD + "cursor-pointer", 
                "title": "Responsible",
            }
        )
    )
    
    wedding_day = forms.DateTimeField(
        label=_("Date of Wedding"),      
        widget=forms.DateTimeInput(
            attrs={
                "class": CLASS_FIELD + " text-right", 
                "type": "datetime-local",
                "title": _("Wait for the date of wedding")
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
        _("Informations"): {
            _("groom"): ["groom_birthday", "groom_birth_place", "groom_last_name", "groom_first_name", "groom_job", "groom_address", "groom_nationality"],
            _("bride"): ["bride_birthday", "bride_birth_place", "bride_last_name", "bride_first_name", "bride_job", "bride_address", "bride_nationality"],
        },
        _("Parent Informations"): {
            _("groom's father"): ["father_groom_exist", "father_groom_pk", "father_groom_last_name", "father_groom_first_name", "father_groom_address", "father_groom_was_alive"],
            _("groom's mother"): ["mother_groom_exist", "mother_groom_pk", "mother_groom_last_name","mother_groom_first_name","mother_groom_address", "mother_groom_was_alive"],
            _("bride's father"): [ "father_bride_exist", "father_bride_pk", "father_bride_last_name", "father_bride_first_name", "father_bride_address", "father_bride_was_alive"],
            _("bride's mother"): ["mother_bride_exist", "mother_bride_pk", "mother_bride_last_name","mother_bride_first_name","mother_bride_address", "mother_bride_was_alive"],
        },
        _("Witnesses Informations"): {
            _("groom's witness"): ["witness_groom_last_name", "witness_groom_first_name", "witness_groom_gender", "witness_groom_birth_place", "witness_groom_birthday", "witness_groom_job", "witness_groom_address",],
            _("bride's witness"): ["witness_bride_last_name", "witness_bride_first_name", "witness_bride_gender", "witness_bride_birth_place", "witness_bride_birthday", "witness_bride_job", "witness_bride_address",],
        },
        _("Register Informations"): ["responsible", "declaration_date","register_date", "wedding_day"],
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