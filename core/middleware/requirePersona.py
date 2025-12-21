from django.shortcuts import redirect
from django.urls import reverse


class RequirePersonaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            if (
                not request.user.persona
                and request.path != reverse('create_profile')
                and not request.path.startswith('/oauth/')
                and not request.path.startswith('/auth/')
                and not request.path.startswith('/admin/')
            ):
                return redirect('create_profile')

        return self.get_response(request)
