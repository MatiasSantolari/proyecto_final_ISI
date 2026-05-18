from django.shortcuts import redirect
from django.contrib import messages
from social_django.views import complete as social_complete
from social_core.exceptions import AuthCanceled, AuthAlreadyAssociated, AuthTokenError
from django.contrib.auth import logout as auth_logout


def oauth_complete_safe(request, backend):
    if request.user.is_authenticated:
        auth_logout(request) 
        
    try:
        return social_complete(request, backend)
        
    except AuthCanceled:
        return redirect('/auth/login/?error=cancelled')
        
    except AuthAlreadyAssociated:
        messages.error(request, "Esta cuenta de Google ya está vinculada a otro usuario del sistema.")
        return redirect('/auth/login/?error=already_associated')
        
    except AuthTokenError:
        messages.error(request, "El token de inicio de sesión de Google expiró. Por favor, intente de nuevo.")
        return redirect('/auth/login/?error=invalid_grant')
        
    except Exception as e:
        messages.error(request, "Ocurrió un error inesperado al conectar con Google.")
        return redirect('/auth/login/?error=unknown')
