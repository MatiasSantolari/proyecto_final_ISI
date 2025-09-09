from core.models import Empleado

class RolActualMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if 'rol_actual' not in request.session or 'empleado_id' not in request.session:
                try:
                    empleado_obj = Empleado.objects.get(usuario=request.user)
                    request.session['rol_actual'] = getattr(request.user, 'rol', 'usuario')
                    request.session['empleado_id'] = empleado_obj.id
                except Empleado.DoesNotExist:
                    request.session['rol_actual'] = getattr(request.user, 'rol', 'usuario')
                    request.session['empleado_id'] = None

        response = self.get_response(request)
        return response
