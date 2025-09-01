from django.urls import include, path
from CommonAdmin import settings, urls
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    print(request.user, request.session['urls'])

    return redirect(request.session['urls'][0]['url'])

def login_page(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """ 
        **Page de connexion** \n
        Permet au visiteur de s'identifier à la base de données.
    """

    request.session.clear()
    
    validated_user = ""
    message = ""

    print(request.GET.get("next"))

    if request.method == "POST":
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)

        if validated_user := authenticate(username=username, password=password):
            login(request, validated_user)

            if not 'urls' in list(request.session.keys()):
                request.session['urls'] = []
                for service in settings.SERVICES_APP:
                    if service["name"] in ("dashboard", "civil", "administration"):
                        request.session['urls'].append(service)
                        
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
    logout(request)
    return redirect("account:index")
