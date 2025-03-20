from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from .forms import LoginForm # Se usa en iniciar_sesion
from django.utils.encoding import force_bytes


def iniciar_sesion(request):
    uidb64 = request.GET.get("uidb64", "") 
    token = request.GET.get("token", "")

    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario")
        password = request.POST.get("password")
        usuario = authenticate(request, username=nombre_usuario, password=password)
        if usuario is not None:
            usuario.ultimo_acceso = timezone.now()
            usuario.save()
            login(request, usuario)
            return redirect("home")
        else:
            messages.error(request, "Usuario y/o Contraseña Incorrectos")
            return redirect('iniciar_sesion')

    return render(request, "iniciar_sesion.html", {
        "uidb64": uidb64,
        "token": token
    })


def recuperar_contrasena(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        User = get_user_model() 
        try:
            user = User.objects.get(correo=email) 
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No hay un usuario registrado con ese correo electrónico.'})

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        domain = get_current_site(request).domain
        ##reset_url = request.build_absolute_uri(reverse('resetear_contrasena', args=[uid, token]))
        reset_url = f"http://{domain}/iniciar_sesion/?modal=nueva_contrasena&uidb64={uid}&token={token}"

        subject = "Recuperación de Contraseña"
        message = render_to_string('reset_email.html', {
            'user': user,
            'reset_url': reset_url
        })
        send_mail(subject, message, 'sanbamerofactory@gmail.com', [user.correo]) 

        messages.success(request, 'Hemos enviado un correo con instrucciones para restablecer tu contraseña.')
        return redirect('iniciar_sesion')

    messages.error(request, 'El correo electronico ingresado no existe.')
    return redirect('iniciar_sesion')


def resetear_contrasena(request, uidb64, token):
    if request.method == "POST":
        User = get_user_model()
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "El enlace de restablecimiento es inválido.")
            return redirect("iniciar_sesion")

        token_valido = default_token_generator.check_token(user, token)

        if not token_valido:
            messages.error(request, "El enlace de restablecimiento ha expirado o es inválido.")
            return redirect("iniciar_sesion")

        nueva_contrasena = request.POST.get("nueva_contrasena")
        confirmar_contrasena = request.POST.get("confirmar_contrasena")

        if nueva_contrasena and nueva_contrasena == confirmar_contrasena:
            user.set_password(nueva_contrasena)
            user.save()
            user.refresh_from_db()  
            messages.success(request, "Tu contraseña ha sido restablecida con éxito. Ahora puedes iniciar sesión.")
            return redirect("iniciar_sesion")
        else:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(f"/iniciar_sesion/?modal=nueva_contrasena&uidb64={uidb64}&token={token}")  

    return redirect("iniciar_sesion")



def index(request): return render(request, 'index.html')
def agregar_sueldo_base(request): return render(request, 'agregar_sueldo_base.html')
def beneficios(request): return render(request, 'beneficios.html')
def calcular_bonificaciones(request): return render(request, 'calcular_bonificaciones.html')
def capacitaciones(request): return render(request, 'capacitaciones.html')
def cargos(request): return render(request, 'cargos.html')
def competencias(request): return render(request, 'competencias.html')
def contratos(request): return render(request, 'contratos.html')
def costos_de_personal(request): return render(request, 'costos_de_personal.html')
def criterios_evaluacion(request): return render(request, 'criterios_evaluacion.html')
def departamentos(request): return render(request, 'departamentos.html')
def empleados(request): return render(request, 'empleados.html')
def evaluacion_desempeno(request): return render(request, 'evaluacion_desempeno.html')
def habilidades(request): return render(request, 'habilidades.html')
def instituciones(request): return render(request, 'instituciones.html')
def logros(request): return render(request, 'logros.html')
def nominas(request): return render(request, 'nominas.html')
def objetivos(request): return render(request, 'objetivos.html')
def personas(request): return render(request, 'personas.html')
def postulantes(request): return render(request, 'postulantes.html')
def publicar_ofertas_de_empleo(request): return render(request, 'publicar_ofertas_de_empleo.html')
def registrar_asistencia(request): return render(request, 'registrar_asistencia.html')
def solicitudes_nuevos_empleados(request): return render(request, 'solicitudes_nuevos_empleados.html')
def tipo_criterio_evaluacion(request): return render(request, 'tipo_criterio_evaluacion.html')
def tipos_contrato(request): return render(request, 'tipos_contrato.html')
def competencias_faltantes(request): return render(request, 'competencias_faltantes.html')
def costos_de_contratacion(request): return render(request, 'costos_de_contratacion.html')
def reporte_evaluacion_desempeno(request): return render(request, 'reporte_evaluacion_desempeno.html')
def contratar_nuevo_empleado(request): return render(request, 'contratar_nuevo_empleado.html')
def ausencias_retardos(request): return render(request, 'ausencias_retardos.html')
