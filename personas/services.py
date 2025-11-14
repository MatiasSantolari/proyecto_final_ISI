import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils.crypto import get_random_string

from core.models import Usuario

logger = logging.getLogger(__name__)


def generar_usuario(persona, email, rol, login_url):
    """
    Crea un usuario asociado a la persona, configura permisos y envía las credenciales.
    """
    password = get_random_string(12)
    username = _generar_username_unico(persona.nombre, persona.apellido)
    print(username, password)

    usuario = Usuario.objects.create_user(
        username=username,
        password=password,
        email=email,
        persona=persona,
        rol=rol,
    )
    
    es_admin = rol == "5"
    usuario.is_staff = es_admin
    usuario.is_superuser = es_admin
    
    usuario.save()

    try:
        send_mail(
            subject="Credenciales de acceso",
            message=(
                f"Hola {persona.nombre},\n\n"
                f"Tu cuenta ha sido creada.\n"
                f"Usuario: {username}\n"
                f"Contraseña temporal: {password}\n\n"
                f"Podés ingresar al sistema desde: {login_url}\n\n"
                "Por favor cambiá tu contraseña luego de ingresar.\n\n"
                "Saludos,\nEl equipo de RRHH"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as error:
        logger.exception("No se pudieron enviar las credenciales: %s", error)

    return usuario


def _generar_username_unico(nombre, apellido):
    base_username = f"{nombre}.{apellido}".replace(" ", "").lower()
    username = base_username
    contador = 1

    while Usuario.objects.filter(username=username).exists():
        username = f"{base_username}{contador}"
        contador += 1

    return username
    