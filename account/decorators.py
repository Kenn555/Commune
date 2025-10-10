from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def permission_required(permission_func):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not permission_func(request.user):
                messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
                if request.user.is_authenticated:
                    raise PermissionDenied
                return redirect('restricted.html')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
