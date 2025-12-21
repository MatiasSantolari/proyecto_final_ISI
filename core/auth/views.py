from django.shortcuts import redirect
from social_django.views import complete as social_complete
from social_core.exceptions import AuthCanceled

def oauth_complete_safe(request, backend):
    try:
        return social_complete(request, backend)
    except AuthCanceled:
        return redirect('/auth/login/?error=cancelled')