from django import forms
from django.utils.translation import gettext_lazy as _
from dal import autocomplete
from datetime import datetime

from administration.models import Fokotany
from civil.models import BirthCertificate, DeathCertificate, MarriageCertificate, Person


CLASS_TEXTFIELD = """
        w-full min-w-52 bg-transparent border-0 border-b-2 border-b-gray-300
        outline-none font-medium text-base tracking-wider
        focus:outline-none focus:border-b-blue-400
        focus:ring-0 focus:ring-offset-0
    """


class BirthCertificateModelForm(forms.ModelForm):
    # Exemple d’autocomplétion avec influence
    fokotany = forms.ModelChoiceField(
        queryset=Fokotany.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="person-autocomplete",
            attrs={"class": CLASS_TEXTFIELD}
        )
    )
    father = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="person-autocomplete",  # à définir dans urls.py
            forward=["fokotany"],       # envoie aussi la valeur du champ "fokotany"
            attrs={"class": CLASS_TEXTFIELD}
        )
    )
    mother = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="person-autocomplete",
            forward=["fokotany"],
            attrs={"class": CLASS_TEXTFIELD}
        )
    )

    class Meta:
        model = Person
        fields = [
            "fokotany", "number",
            "last_name", "first_name", "gender", "birth_place", "birthday",
            "father", "mother",
        ]
        widgets = {
            "fokotany": forms.Select(attrs={"class": CLASS_TEXTFIELD + " text-lg cursor-pointer"}),
            "number": forms.TextInput(attrs={"class": CLASS_TEXTFIELD + " text-center text-lg tracking-widest cursor-pointer text-gray-500"}),
            "last_name": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "first_name": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "gender": forms.Select(attrs={"class": CLASS_TEXTFIELD}),
            "birth_place": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "birthday": forms.DateTimeInput(
                attrs={"class": CLASS_TEXTFIELD + " text-right", "type": "datetime-local"}
            ),
        }

    # ---- Tes fieldsets personnalisés ----
    fieldsets = {
        _("Matricule"): ["fokotany", "number"],
        _("Informations"): ["last_name", "first_name", "gender", "birth_place", "birthday"],
        _("Parents"): ["father", "mother"],
    }

    @property
    def fieldsets_fields(self):
        fs = {}
        for title, fields in self.fieldsets.items():
            fs[title] = [self[ch] for ch in fields]
        return fs


class DeathCertificateForm(forms.ModelForm):
    class Meta:
        model = DeathCertificate
        fields = ["last_name", "first_name", "date_of_death", "place_of_death"]
        widgets = {
            "last_name": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "first_name": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "date_of_death": forms.DateTimeInput(
                attrs={"class": CLASS_TEXTFIELD + " text-right", "type": "datetime-local"}
            ),
            "place_of_death": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
        }

    fieldsets = {
        _("Informations"): ["last_name", "first_name", "date_of_death", "place_of_death"],
    }

    @property
    def fieldsets_fields(self):
        return {title: [self[ch] for ch in fields] for title, fields in self.fieldsets.items()}


class MarriageCertificateForm(forms.ModelForm):
    class Meta:
        model = MarriageCertificate
        fields = ["last_name_man", "first_name_man", "date_of_marriage", "place_of_marriage"]
        widgets = {
            "last_name_man": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "first_name_man": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
            "date_of_marriage": forms.SelectDateWidget(years=range(1900, 2026)),
            "place_of_marriage": forms.TextInput(attrs={"class": CLASS_TEXTFIELD}),
        }

    fieldsets = {
        _("Informations Mariage"): ["last_name_man", "first_name_man", "date_of_marriage", "place_of_marriage"],
    }

    @property
    def fieldsets_fields(self):
        return {title: [self[ch] for ch in fields] for title, fields in self.fieldsets.items()}
