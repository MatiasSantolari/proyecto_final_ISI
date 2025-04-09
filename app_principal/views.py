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
from django.utils.encoding import force_bytes
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from .forms import PersonaForm, CargoForm, LoginForm
from .models import Persona, Empleado, Solicitud, EmpleadoCargo, Cargo, HistorialSueldoBase


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


################## CRUD PERSONA ################
def personas(request):
    personas_qs = Persona.objects.select_related('empleado')
    
    personas_con_datos = []

    for persona in personas_qs:
        estado = ""
        cargo_id = ""
        nombre_cargo = ""

        if persona.tipo_persona == 'empleado' and hasattr(persona, 'empleado'):
            estado = persona.empleado.estado

            # Obtenemos el último cargo desde el empleado
            ultimo_cargo = persona.empleado.empleadocargo_set.order_by('fecha_asignacion').last()
            if ultimo_cargo:
                cargo_id = ultimo_cargo.cargo.id_cargo
                nombre_cargo = ultimo_cargo.cargo.nombre

        personas_con_datos.append({
            'id': persona.id_persona,
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'dni': persona.dni,
            'email': persona.email,
            'telefono': persona.telefono,
            'fecha_nacimiento': persona.fecha_nacimiento,
            'direccion': persona.direccion,
            'tipo_persona': persona.tipo_persona,
            'estado': estado,
            'cargo': cargo_id,
            'nombre_cargo': nombre_cargo,
        })

    form = PersonaForm()
    return render(request, 'personas.html', {'personas': personas_con_datos, 'form': form})




def crear_persona(request):
    if request.method == 'POST':
        id_persona = request.POST.get('id_persona')

        if id_persona:
            persona = get_object_or_404(Persona, id_persona=id_persona)
            form = PersonaForm(request.POST, instance=persona)
        else:
            form = PersonaForm(request.POST)

        if form.is_valid():
            tipo_persona = form.cleaned_data.get('tipo_persona')
            estado_empleado = form.cleaned_data.get('estado')
            cargo = form.cleaned_data.get('cargo')

            if tipo_persona == 'empleado':
                if id_persona:
                    # Buscar si ya existe como empleado
                    empleado = Empleado.objects.filter(id_persona=id_persona).first()

                    if empleado:
                        # Actualizar campos del empleado
                        empleado.nombre = form.cleaned_data['nombre']
                        empleado.apellido = form.cleaned_data['apellido']
                        empleado.dni = form.cleaned_data['dni']
                        empleado.email = form.cleaned_data['email']
                        empleado.telefono = form.cleaned_data['telefono']
                        empleado.fecha_nacimiento = form.cleaned_data['fecha_nacimiento']
                        empleado.direccion = form.cleaned_data['direccion']
                        empleado.tipo_persona = 'empleado'
                        empleado.estado = estado_empleado
                        empleado.save()
                    else:
                        # No existía como empleado, convertirlo
                        persona = form.save(commit=False)
                        empleado = Empleado.objects.create(
                            id_persona=id_persona,
                            nombre=persona.nombre,
                            apellido=persona.apellido,
                            dni=persona.dni,
                            email=persona.email,
                            telefono=persona.telefono,
                            fecha_nacimiento=persona.fecha_nacimiento,
                            direccion=persona.direccion,
                            tipo_persona='empleado',
                            estado=estado_empleado
                        )

                    if cargo:
                        EmpleadoCargo.objects.update_or_create(
                            empleado=empleado,
                            defaults={'cargo': cargo, 'fecha_asignacion': date.today()}
                        )
                else:
                    # Nueva persona y empleado
                    empleado = Empleado.objects.create(
                        nombre=form.cleaned_data['nombre'],
                        apellido=form.cleaned_data['apellido'],
                        dni=form.cleaned_data['dni'],
                        email=form.cleaned_data['email'],
                        telefono=form.cleaned_data['telefono'],
                        fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                        direccion=form.cleaned_data['direccion'],
                        tipo_persona='empleado',
                        estado=estado_empleado
                    )
                    if cargo:
                        EmpleadoCargo.objects.create(
                            empleado=empleado,
                            cargo=cargo,
                            fecha_asignacion=date.today()
                        )
            else:
                # Si es postulante u otro tipo de persona
                form.save()

            return redirect('personas')
        else:
            print("Errores en el formulario:", form.errors)
    else:
        form = PersonaForm()

    personas = Persona.objects.all()
    return render(request, 'personas.html', {'form': form, 'personas': personas})



def obtener_datos_persona(request, persona_id):
    try:
        persona = Persona.objects.get(id_persona=persona_id)
        data = {
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'dni': persona.dni,
            'email': persona.email,
            'telefono': persona.telefono,
            'fecha_nacimiento': persona.fecha_nacimiento.strftime('%Y-%m-%d'),
            'direccion': persona.direccion,
            'tipo_persona': persona.tipo_persona,
        }

        if persona.tipo_persona == 'empleado':
            empleado = Empleado.objects.get(id_persona=persona_id)
            data['estado_empleado'] = empleado.estado
            if empleado.empleadocargo_set.exists():
                ultimo_cargo = empleado.empleadocargo_set.last()
                data['cargo'] = ultimo_cargo.cargo_id
                data['cargo_nombre'] = ultimo_cargo.cargo.nombre
            else:
                data['cargo'] = ''
                data['cargo_nombre'] = ''
        return JsonResponse(data)

    except Persona.DoesNotExist:
        return JsonResponse({'error': 'Persona no encontrada'}, status=404)


@require_POST
def eliminar_persona(request, persona_id):
    persona = get_object_or_404(Persona, id_persona=persona_id)
    persona.delete()
    return redirect('personas')



########## CRUD CARGO #################

def cargos(request):
    cargos = Cargo.objects.all()
    form = CargoForm()
    cargos_con_sueldo = []

    for cargo in cargos:
        ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo).order_by('-fecha_sueldo').first()
        sueldo = ultimo_sueldo.sueldo_base if ultimo_sueldo else None

        cargos_con_sueldo.append({
            'id': cargo.id_cargo,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
        })
    return render(request, 'cargos.html', {'cargos': cargos_con_sueldo, 'form': form})


def crear_cargo(request):
    if request.method == 'POST':
        id_cargo = request.POST.get('id_cargo')
        
        if id_cargo:
            cargo = get_object_or_404(Cargo, pk=id_cargo)
            form = CargoForm(request.POST, instance=cargo)
        else:
            form = CargoForm(request.POST)

        if form.is_valid():
            cargo_guardado = form.save()
            sueldo_base = form.cleaned_data['sueldo_base']
            ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo_guardado).order_by('-fecha_sueldo').first()
            if not ultimo_sueldo or ultimo_sueldo.sueldo_base != sueldo_base:
                HistorialSueldoBase.objects.create(
                    cargo=cargo_guardado,
                    sueldo_base=sueldo_base,
                    fecha_sueldo=timezone.now()
                )
            return redirect('cargos')
    else:
        form = CargoForm()
    return render(request, 'cargos.html', {'form': form})


@require_POST
def eliminar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id_cargo=cargo_id)
    cargo.delete()
    return redirect('cargos')





def index(request): return render(request, 'index.html')
def agregar_sueldo_base(request): return render(request, 'agregar_sueldo_base.html')
def beneficios(request): return render(request, 'beneficios.html')
def calcular_bonificaciones(request): return render(request, 'calcular_bonificaciones.html')
def capacitaciones(request): return render(request, 'capacitaciones.html')
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
