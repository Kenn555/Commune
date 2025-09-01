from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from CommonAdmin.settings import COMMON_NAME
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest


# Create your views here.
@login_required
def index(request: WSGIRequest) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    """  """

    title = ""    
    current_app = request.path.split("/")[1]

    for service in request.session['urls']:  
        if service['name'] == current_app:
            title = service['title']

    context = {
        "user": request.user,
        "title": title,
        "services": request.session['urls'],
        "common_name": COMMON_NAME,
    }

    return render(request, current_app + "/home.html", context)