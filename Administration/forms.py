from django import forms
from django.utils.translation import gettext_lazy as _

from account.models import User
from administration.models import Application, Role, Service, Staff


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
                "title": "0000000001",
                "title": "Matricule",
            }
        )
    )

    first_name = forms.CharField(
        label=_("First Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his last name"),
            }
        )
    )

    username = forms.CharField(
        label=_("Username"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his username"),
            }
        )
    )

    password = forms.CharField(
        label=_("Password"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his password"),
            }
        )
    )

    email = forms.EmailField(
        label=_("Email"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his email"),
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["number"],
        _("Informations"): ["last_name", "first_name", "email",],
        _("Logins"): ["username", "password",],
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
    

class StaffForm(forms.Form):    
    number = forms.CharField(
        label=_("Number"), 
        disabled=True,
        initial="1".zfill(9) if not User.objects.count() else str(User.objects.last().id + 1).zfill(9),
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD.replace("w-full min-w-52", "w-36 text-gray-500") + " text-center text-lg tracking-widest cursor-pointer", 
                "title": "Matricule",
            }
        )
    )

    first_name = forms.CharField(
        label=_("First Name"), 
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_staff", 
                "title": _("Insert her/his first name"),
            }
        )
    )
    
    last_name = forms.CharField(
        label=_("Last Name"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD + " searched_staff", 
                "title": _("Insert her/his last name"),
            }
        )
    )
    
    gender = forms.ChoiceField(
        label=_("Gender"), 
        choices=Staff.GENDER_CHOICES,
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Choose the gender")
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
                "title": _("Enter/Choose the date of birth")
            }
        )
    )
    
    contact_1 = forms.CharField(
        label=_("Contact 1"), 
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his first contact"),
            }
        )
    )
    
    contact_2 = forms.CharField(
        label=_("Contact 2"),
        required=False,
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his second contact"),
            }
        )
    )

    email = forms.EmailField(
        label=_("Email"), 
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his email"),
            }
        )
    )

    title = forms.ModelChoiceField(
        label=_("Title"),
        queryset=Role.objects.all().order_by('service__grade', 'grade'),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Select a Application..."),
            }
        )
    )

    username = forms.CharField(
        label=_("Username"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his username"),
            }
        )
    )

    password = forms.CharField(
        label=_("Password"), 
        widget=forms.PasswordInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his password"),
            }
        )
    )

    fieldsets = {
        _("Matricule"): ["number"],
        _("Informations"): ["last_name","first_name","email","gender","birthday","contact_1","contact_2",],
        _("Role"): ["title"],
        # _("Role"): ["title", "description", "application", "service", "is_boss"],
        _("Logins"): ["username", "password",],
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


class RoleForm(forms.Form):
    title = forms.CharField(
        label=_("Title"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his role"),
            }
        )
    )

    description = forms.CharField(
        label=_("Description"), 
        widget=forms.TextInput(
            attrs={
                "class": CLASS_FIELD, 
                "title": _("Insert her/his title"),
            }
        )
    )

    service = forms.ModelChoiceField(
        label=_("Service"),
        queryset=Service.objects.all().order_by('title'),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Select a Service..."),
            }
        )
    )

    grade = forms.IntegerField(
        label=_("Grade"),
        min_value=1,
        initial=2,
        widget=forms.NumberInput(
            attrs={
                "class": CLASS_FIELD + " text-center",
                "title": _("Insert the Grade in the Service"),
            }
        )
    )

    application = forms.ModelChoiceField(
        label=_("Application"),
        queryset=Application.objects.all(),
        widget=forms.Select(
            attrs={
                "class": CLASS_FIELD,
                "title": _("Select a Application..."),
            }
        )
    )