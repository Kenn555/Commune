from datetime import date, timedelta, timezone
from pyexpat.errors import messages
from django.urls import reverse_lazy
from django.views.generic import DetailView, DeleteView

import django.db.utils
from administration.models import Fokotany
from django.db.models import Q
from civil import forms
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from dal import autocomplete

from civil.forms import BirthCertificateForm, DeathCertificateForm, MarriageCertificateForm
from civil.models import BirthCertificate, CertificateDocument, Person


CERTIFICATE = {
    "birth": BirthCertificateForm,
    "death": DeathCertificateForm,
    "marriage": MarriageCertificateForm,
}

FOKOTANY = Fokotany.objects.all()

actions = [
    {
        'name': "list",
        'title': "",
        'url': ""
    },
    {
        'name': "register",
        'title': "",
        'url': ""
    },
]

def add_action_url(app, menu_name):
    for action in actions:
        if action['name'] == 'list':
            action['title'] = _("list")
            action['url'] = app + ":" + menu_name
        elif action['name'] == 'register':
            action['title'] = _("register")
            action['url'] = app + ":" + menu_name + "-register"

class PersonAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete pour rechercher des personnes existantes"""
    
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Person.objects.none()

        qs = Person.objects.all()

        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )

        return qs.order_by('last_name', 'first_name')

    def get_result_label(self, item):
        """Format d'affichage dans la liste déroulante"""
        return _("%(last_name)s %(first_name)s - born at %(birthday_day)s at %(birthday_hour)s.") % {
            "last_name": item.last_name, 
            "first_name": item.first_name, 
            "birthday_day": item.birthday.strftime('%d/%m/%Y'),
            "birthday_hour": item.birthday.strftime('%H:%M')
        }


class FatherAutocomplete(PersonAutocomplete):
    """Autocomplete spécifique pour les pères"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        print(qs)
        return qs.filter(gender='M', birthday__lte=date.today() - timedelta(days=18*365))


class MotherAutocomplete(PersonAutocomplete):
    """Autocomplete spécifique pour les mères"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(gender='F', birthday__lte=date.today() - timedelta(days=18*365))

@login_required 
def get_person_details(request, person_id):
    """Retourne les détails d'une personne en JSON"""
    try:
        person = Person.objects.get(id=person_id)
        
        data = {
            'full_name': person.full_name,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'birthday': person.birthday.strftime('%Y-%m-%dT%H:%M'),
            'birth_place': person.birth_place,
            'gender': person.gender,
        }
        
        return JsonResponse(data)
    except Person.DoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    
# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """
    
    print(request.session['urls'])

    menu_name = "dashboard"
    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "text": [],
        "birth_count": BirthCertificate.objects.count()
    }

    for certificate in BirthCertificate.objects.all():
        context['text'].append(certificate)

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])
    print(context['services'])

    return render(request, "civil/dashboard.html", context)

@login_required
def birth_list(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "birth"
    
    add_action_url(__package__, menu_name)

    line_bypage = str(request.GET.get('line', 10))

    # Tous les Certificats
    certificates_data = BirthCertificate.objects.all()

    # Recherche
    if 'q' in request.GET.keys():
        certificates_data = certificates_data.filter(
                    Q(born__first_name__icontains=request.GET['q']) |
                    Q(born__last_name__icontains=request.GET['q'])
                )

    # Ordre
    certificates_data = certificates_data.order_by("pk").reverse()

    # Pagination
    certificate_bypage = Paginator(certificates_data, line_bypage)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "list",
        "actions": actions,
        "table_length": line_bypage,
        "table": {
            "headers": [_("date of creation"), _("number"), _("full name"), _("gender"), _("age"), _("birthday"), _("father"), _("mother"), _("fokotany"), _("action")], 
            "datas": [
                {                                
                    "index" : index,
                    "pk": (CertificateDocument.objects.filter(birth_certificate=birth).first()).pk if CertificateDocument.objects.filter(birth_certificate=birth).exists() else int(birth.pk),
                    "row": [
                        {"header": "date", "value": birth.date_created, "style": "text-start w-4 text-nowrap", "title": birth.date_created},
                        {"header": "number", "value": str(birth.pk).zfill(9), "style": "text-center w-12 text-nowrap", "title": str(birth.pk).zfill(9)},
                        {"header": "full name", "value": birth.born.full_name, "style": "text-start w-4 text-nowrap", "title": birth.born.full_name},
                        {"header": "gender", "value": Person.GENDER_CHOICES[birth.born.gender], "style": "text-center text-nowrap", "title": Person.GENDER_CHOICES[birth.born.gender]},
                        {"header": "age", "value": date.today().year - birth.born.birthday.year, "style": "text-center text-nowrap", "title": ngettext("%(age)d year old", "%(age)d years old", date.today().year - birth.born.birthday.year) % {"age": date.today().year - birth.born.birthday.year}},
                        {"header": "date", "value": birth.born.birthday, "style": "text-start w-4 text-nowrap", "title": birth.born.birthday},
                        {"header": "father", "value": birth.father.full_name, "style": "text-start w-4 text-nowrap", "title": birth.father.full_name},
                        {"header": "mother", "value": birth.mother.full_name, "style": "text-start w-4 text-nowrap", "title": birth.mother.full_name},
                        {"header": "fokotany", "value": birth.fokotany.name, "style": "text-start w-4 text-nowrap", "title": birth.fokotany},
                        {"header": "action", "style": "bg-rose-600", "title": "", "buttons": [
                            {"name": _("open"), "url": "civil:certificate-print", "style": "green"},
                            {"name": _("print"), "url": "civil:certificate-preview", "style": "blue"},
                            # {"name": _("delete"), "url": "civil:birth-delete", "style": "red"},
                        ]},
                    ],
                } for index, birth in enumerate(certificate_bypage.get_page(1))
            ],
        }
    }

    print(actions)

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    print(context['menu_title'], context['action_name'])

    return render(request, "civil/list.html", context)

@login_required
def birth_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "birth"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": CERTIFICATE[menu_name](),
        "register_manager": __package__ + ":register_manager",
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "actions": actions
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/register.html", context)

@login_required
def birth_save(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    
    print(request.POST.keys())
        
    form = BirthCertificateForm(request.POST)
    person_datas = form.fieldsets_fields[_('Informations')]
    print(form.data)

    if form.data:
        # Table Fokotany
        fokotany = Fokotany.objects.get(pk=form.fieldsets_fields[_('Matricule')][0].data)
        # Table Personne
        born = Person(Person.objects.last().id + 1 if Person.objects.last() else 1, *[person_data.data for person_data in person_datas])

        print(born.birthday)

        if "do_certificate" in request.POST:
            print(request.POST['do_certificate'])
            # Si le père existe
            if "use_existing_father" in request.POST:
                print(request.POST['existing_father'])
                father = Person.objects.get(pk=request.POST['existing_father'])
                print(father)
                father_carreer = request.POST['father_job']
                certificate_type = list(BirthCertificate.CERTIFICATE_TYPES.keys())[1]
                if father and not father.is_parent:
                    father.is_parent = True
            else:
                father = None
                father_carreer = None
                certificate_type = list(BirthCertificate.CERTIFICATE_TYPES.keys())[0]
            # Si la mère existe
            if "use_existing_mother" in request.POST:
                print(request.POST['existing_mother'])
                mother = Person.objects.get(pk=request.POST['existing_mother'])
                print(mother)
                mother_carreer = request.POST['mother_job']
                if not mother.is_parent:
                    mother.is_parent = True
            # déclarant
            print(request.POST['existing_declarer'])
            declarer = Person.objects.get(pk=request.POST['existing_declarer'])
            print(declarer)
            declarer_carreer = request.POST['declarer_job']
        else:
            print(born.pk, born.full_name)

        print(form.errors)

        # Table BirthCertificate
        if form.is_valid():
            try:
                born.save()
            except django.db.utils.IntegrityError:
                born = Person.objects.get(last_name=born.last_name, first_name=born.first_name, gender=born.gender, birthday=born.birthday)

            certificate = BirthCertificate(
                BirthCertificate.objects.last().id + 1 if BirthCertificate.objects.last() else 1,
                fokotany = fokotany,
                born = born,
                father = father,
                father_carreer = father_carreer,
                mother = mother,
                mother_carreer = mother_carreer,
                declarer = declarer,
                declarer_carreer = declarer_carreer,
                certificate_type = certificate_type,
            )

            print(certificate)
            print(father.is_parent, mother.is_parent)
            print(certificate)
            # Mettre à jour le statut de parent
            certificate.save()
            CertificateDocument.objects.create(
                        birth_certificate=certificate,
                        document_number=f"BC-{fokotany.pk}-{certificate.date_created.year}-{str(certificate.pk).zfill(9)}",
                        status='DRAFT'
                    )
            father.save(update_fields=["is_parent"])
            mother.save(update_fields=["is_parent"])

            return redirect('civil:birth')
        else:
            born.save()

            return redirect('civil:birth-register')
    ...

@login_required
def birth_detail(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("DETAILLE !!!!!!!!!!!!!!!!!!!")
    context = {}
    return render(request, "civil/certificate.html", context)

@login_required
def birth_modify(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:

    print("MODIFIE !!!!!!!!!!!!!!!!!!!")
    return redirect('civil:birth')

@login_required
def birth_delete(request: WSGIRequest, birth_id) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    print(BirthCertificate.objects.get(pk=birth_id).delete())
    print("SUPPRIME !!!!!!!!!!!!!!!!!!!")
    return redirect('civil:birth')

@login_required
def certificate_preview(request: WSGIRequest, pk) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    menu_name = "birth"
    document = get_object_or_404(CertificateDocument, pk=pk)

    print(document.birth_certificate.born.birthday)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": CERTIFICATE[menu_name](),
        "register_manager": __package__ + ":register_manager",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "actions": actions,
        "document": document,
        "certificate": document.birth_certificate
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/preview.html", context)

def certificate_print_view(request, pk):
    """Vue pour l'impression (version simplifiée sans boutons)"""
    document = get_object_or_404(CertificateDocument, pk=pk)
    return render(request, 'civil/print_view.html', {
        'document': document,
        'certificate': document.birth_certificate,
    })


def certificate_validate(request, pk):
    """Valider un certificat"""
    document = get_object_or_404(CertificateDocument, pk=pk)
    
    if document.can_edit:
        document.status = 'VALIDATED'
        document.validated_by = request.user.get_full_name() or request.user.username
        document.validated_at = timezone.now()
        document.save()
        messages.success(request, _('Certificate validated successfully.'))
    else:
        messages.error(request, _('This certificate cannot be validated.'))
    
    return redirect('certificate-preview', pk=pk)


class CertificateDeleteView(DeleteView):
    """Vue pour supprimer un certificat"""
    model = CertificateDocument
    success_url = reverse_lazy('certificate-list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if not self.object.can_delete:
            messages.error(request, _('This certificate cannot be deleted.'))
            return redirect('certificate-preview', pk=self.object.pk)
        
        messages.success(request, _('Certificate deleted successfully.'))
        return super().delete(request, *args, **kwargs)

@login_required
def death(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "death"
    
    add_action_url(__package__, menu_name)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "list",
        "actions": actions,
        "table": {
            "headers": ["Nom", "Prénom", "Genre", "Âge"], 
            "rows": [
                {"datas": ["BEZARA", "Kenn Keren", "Homme", "24"]},
                {"datas": ["BEZARA", "Kenn Keren", "Homme", "24"]},
            ],
        },
        "table_length": "50",
    }

    # Requêtes GET
    if request.method == "GET":
        # Nombre de lignes du tableau
        if "line" in request.GET.keys():
            context['table_length'] = request.GET.get("line")

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    print(context['menu_title'])

    return render(request, "civil/list.html", context)


@login_required
def death_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "death"
    
    add_action_url(__package__, menu_name)

    request.session['menu_app'] = menu_name

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": CERTIFICATE[menu_name](),
        "register_manager": __package__ + ":register_manager",
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "actions": actions
    }

    if context['form'].is_valid():
        print(context["form"].clear_data)
    
    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/register.html", context)

@login_required
def marriage(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    add_action_url(__package__, menu_name)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "page_urls": {"list": __package__ + ":" + menu_name, "register": __package__ + ":" + menu_name + "-register"},
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "list",
        "actions": actions
    }

    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/list.html", context)

@login_required
def marriage_register(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    menu_name = "marriage"

    add_action_url(__package__, menu_name)

    context = {
        "user": request.user,
        "app_name": __package__,
        "menu_name": menu_name,
        "form": MarriageCertificateForm(),
        "services": request.session['urls'],
        "common_name": getattr(settings, "COMMON_NAME"),
        "submenus": [],
        "action_name": "register",
        "actions": actions
    }
    
    for service in request.session['urls']:
        if service['name'] == __package__:
            context['title'] = _(service['title'])
            if 'submenus' in list(service.keys()):
                context['submenus'] += service['submenus']
                for submenu in service['submenus']:
                    if submenu['name'] == menu_name:
                        context['menu_title'] = _(submenu['title'])

    return render(request, "civil/register.html", context)

@login_required
def register_manager(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    print(request.POST)

    form = BirthCertificateForm(request.POST)
    menu_app = request.session['menu_app']

    print(menu_app, form.is_valid(), form.errors)

    if form.is_valid():
        for field, value in form.cleaned_data.items():
            print(field, ":", value)
        request.session['menu_app'] = None

    return redirect(f"civil:{menu_app}-register")
    ...