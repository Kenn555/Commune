from django.urls import include, path
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings

from administration.models import Role
# from django.contrib.auth.models import Group
# from django.contrib import messages
# from .permissions import create_groups_and_permissions
# from .decorators import permission_required as custom_permission_required
# from .permissions import has_civil_permission, has_finance_permission

User = get_user_model()

# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """
    if 'urls' in list(request.session.keys()):
        return redirect(request.session['urls'][0]['url'])
    else:
        return redirect("account:login")

def login_page(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """ 
        **Page de connexion** \n
        Permet au visiteur de s'identifier à la base de données.
    """
    # Si l'utilisateur est déjà connecté, le rediriger
    if request.user.is_authenticated:
        return redirect("account:index")

    # Nettoyer la session existante
    request.session.flush()
    request.session['app_accessed'] = []
    
    validated_user = ""
    message = ""

    if request.method == "POST":
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)

        if validated_user := authenticate(username=username, password=password):
            # Créer une nouvelle session
            login(request, validated_user)
            request.session.set_expiry(0)  # La session expire à la fermeture du navigateur

            # Initialiser les URLs de service
            if not 'urls' in list(request.session.keys()):
                request.session['urls'] = []
                for service in getattr(settings, "SERVICES_APP"):
                    if validated_user.is_superuser and service["name"] in ("dashboard", "civil", "mines", "events", "administration"):
                        request.session['urls'].append(service)
                    elif service["name"] == Role.objects.get(access=validated_user).app.name:
                        request.session['urls'].append(service)
                        settings

            for app in request.session['urls']:
                request.session['app_accessed'].append(app['name'])

                        
            # Gérer la redirection
            if request.GET.get("next"):
                next_app = request.GET.get('next').split('/')[1]
                if next_app != "":
                    return redirect(f"{next_app}:index")

            return redirect("account:index")
            ...
        else:
            message = "Nom d'utilisateur ou Mot de passe incorrect"

    context = {
        "message": message,
        "user": validated_user,
    }

    return render(request, "authentification/login.html", context)

def logout_page(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """Déconnexion de l'utilisateur et nettoyage de la session"""
    request.session.flush()  # Nettoie complètement la session
    logout(request)  # Déconnexion de l'utilisateur
    return redirect("account:login")  # Redirection vers la page de connexion

# @login_required
# @permission_required('auth.add_user')
# def manage_users(request: WSGIRequest) -> HttpResponse:
#     """Gestion des utilisateurs et de leurs permissions"""
#     if request.method == "POST":
#         action = request.POST.get('action')
#         user_id = request.POST.get('user_id')
#         group_id = request.POST.get('group_id')
        
#         user = get_object_or_404(User, id=user_id)
#         group = get_object_or_404(Group, id=group_id)
        
#         if action == 'add_to_group':
#             user.groups.add(group)
#             messages.success(request, f"L'utilisateur {user.username} a été ajouté au groupe {group.name}")
#         elif action == 'remove_from_group':
#             user.groups.remove(group)
#             messages.success(request, f"L'utilisateur {user.username} a été retiré du groupe {group.name}")
            
#     # Assurer que les groupes et permissions existent
#     create_groups_and_permissions()
    
#     users = User.objects.all().prefetch_related('groups')
#     groups = Group.objects.all().prefetch_related('permissions')
    
#     context = {
#         'users': users,
#         'groups': groups,
#     }
    
#     return render(request, 'account/manage_users.html', context)
