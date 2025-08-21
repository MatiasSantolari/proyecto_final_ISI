class RolActualMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if 'rol_actual' not in request.session:
                request.session['rol_actual'] = request.user.rol
        response = self.get_response(request)
        return response