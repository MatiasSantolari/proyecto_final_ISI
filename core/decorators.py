from django.http import HttpResponseForbidden
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('rol_actual') == 'admin':
            return view_func(request, *args, **kwargs)
        messages.error(request, "Acceso denegado. No tenés permisos de administrador para ver esta sección.")
        return redirect('home')
    return _wrapped_view


def rol_requerido(*roles_permitidos):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
        return _wrapped_view
    return decorator



def asegurar_rol_actual(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Si no existe rol_actual, usar el rol real del usuario
            if 'rol_actual' not in request.session or not request.session['rol_actual']:
                request.session['rol_actual'] = request.user.rol
        return view_func(request, *args, **kwargs)
    return _wrapped_view







# De Core.Middleware

#class RolActualMiddleware:
#    def __init__(self, get_response):
#        self.get_response = get_response
#
#    def __call__(self, request):
#        if request.user.is_authenticated:
#            if 'rol_actual' not in request.session:
#                request.session['rol_actual'] = request.user.rol
#        response = self.get_response(request)
#        return response