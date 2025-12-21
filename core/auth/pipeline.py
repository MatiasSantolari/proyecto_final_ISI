from django.shortcuts import redirect
from django.urls import reverse
from ..models import Persona 

def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == 'google-oauth2' or not user:
        return
    picture = response.get('picture')
    if picture:
        backend.strategy.session_set('google_avatar', picture)




def require_persona(strategy, user=None, response=None, *args, **kwargs):
    if not user:
        return

    if hasattr(user, 'persona') and user.persona:
        return

    google_data = {
        'nombre': response.get('given_name', ''),
        'apellido': response.get('family_name', ''),
        'email': response.get('email', ''),
        'picture': response.get('picture'),
    }

    try:
        social = user.social_auth.get(provider='google-oauth2')
        social.extra_data.update(google_data)
        social.save()
    except Exception as e:
        print(f"ERROR: No se pudo encontrar o guardar social_auth: {e}")
