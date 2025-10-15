from django import forms
from django.utils.translation import gettext_lazy as _

from account.models import User


CLASS_FIELD = """
        w-full bg-transparent border-0 border-b-2 border-b-gray-300
        outline-none font-medium text-base tracking-wider
        focus:outline-none focus:border-b-blue-400
        focus:ring-0 focus:ring-offset-0
    """

class UserForm(forms.Form):    
    number = forms.CharField(
        label=_("Number"), 
        disabled=True,
        initial="1".zfill(9) if not User.objects.count() else str(User.objects.last().id + 1).zfill(9),
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD.replace("w-full min-w-52", "w-36 text-gray-500") + " text-center text-lg tracking-widest cursor-pointer", 
                "placeholder": "0000000001",
                "title": "Matricule",
            }
        )
    )

    first_name = forms.CharField(
        label=_("First Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his first name"),
                "title": _("Insert her/his first name"),
            }
        )
    )
    
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

    username = forms.CharField(
        label=_("Username"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his username"),
                "title": _("Insert her/his username"),
            }
        )
    )

    password = forms.CharField(
        label=_("Password"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his password"),
                "title": _("Insert her/his password"),
            }
        )
    )

    email = forms.EmailField(
        label=_("Email"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "placeholder": _("Insert her/his email"),
                "title": _("Insert her/his email"),
            }
        )
    )

    civil = forms.BooleanField(
        label=_("civil status").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    events = forms.BooleanField(
        label=_("events").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    finances = forms.BooleanField(
        label=_("finances").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    mines = forms.BooleanField(
        label=_("mines").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    administration = forms.BooleanField(
        label=_("administration").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    social = forms.BooleanField(
        label=_("social").title(),
        required=False,
        label_suffix="",
        widget=forms.CheckboxInput(attrs={"class": "mr-2"})
    )

    fieldsets = {
        _("Matricule"): ["number"],
        _("Informations"): ["last_name", "first_name", "email",],
        _("Logins"): ["username", "password",],
        _("Applications"): ["civil", "events", "finances", "mines", "social", "administration"],
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