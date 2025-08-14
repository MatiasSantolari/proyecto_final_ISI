import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from ..models import *
from ..forms import *
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
from django.contrib.auth.decorators import login_required
from ..decorators import rol_requerido
from django.utils.timezone import now
from collections import defaultdict
from django.contrib.admin.views.decorators import staff_member_required

def personas(request):
    personas_qs = Persona.objects.select_related('empleado', 'usuario')

    personas_con_datos = []

    for persona in personas_qs:
        estado = ""
        cargo_id = ""
        nombre_cargo = ""
        tipo_usuario = ""
        departamento_id = ""
        departamento_nombre = ""

        # Si tiene usuario relacionado, extraemos el rol
        if hasattr(persona, 'usuario'):
            tipo_usuario = persona.usuario.rol

            # Si el rol es de tipo empleado o superior y tiene relación con Empleado
            if tipo_usuario in ['empleado', 'jefe', 'gerente', 'admin'] and hasattr(persona, 'empleado'):
                estado = persona.empleado.estado

                # Obtenemos el último cargo
                ultimo_cargo = persona.empleado.empleadocargo_set.order_by('fecha_inicio').last()
                if ultimo_cargo:
                    cargo = ultimo_cargo.cargo
                    cargo_id = cargo.id
                    nombre_cargo = cargo.nombre

                    # Buscar departamento asociado al cargo desde la tabla intermedia
                    cargo_departamento = CargoDepartamento.objects.filter(cargo=cargo).first()
                    if cargo_departamento:
                        departamento_id = cargo_departamento.departamento.id
                        departamento_nombre = cargo_departamento.departamento.nombre
            else:
                estado = "Sin Estado"
                nombre_cargo = "Sin Cargo"

        personas_con_datos.append({
            'id': persona.id,
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'dni': persona.dni,
            'email': persona.usuario.email,
            'prefijo_pais': persona.prefijo_pais,
            'telefono': persona.telefono,
            'fecha_nacimiento': persona.fecha_nacimiento,
            'genero': persona.genero,
            'pais': persona.pais,
            'provincia': persona.provincia,
            'ciudad': persona.ciudad,
            'calle': persona.calle,
            'numero': persona.numero,
            'tipo_usuario': tipo_usuario,
            'estado': estado,
            'cargo': cargo_id,
            'nombre_cargo': nombre_cargo,
            'departamento_id': departamento_id,
            'departamento_nombre': departamento_nombre,

            'telefono_completo': persona.prefijo_pais + persona.telefono,
        })

    form = PersonaForm()
    return render(request, 'personas.html', {'personas': personas_con_datos, 'form': form})


def crear_persona(request):
    if request.method == 'POST':
        id_persona = request.POST.get('id_persona')
        persona = get_object_or_404(Persona, id=id_persona) if id_persona else None
        departamento_id = request.POST.get('departamento')

        form = PersonaForm(request.POST, request.FILES, instance=persona, departamento_id=departamento_id)

        if form.is_valid():
            email = form.cleaned_data.get('email')

            if not id_persona and Usuario.objects.filter(email=email).exists():
                form.add_error('email', 'Ya existe un usuario registrado con ese correo electrónico.')
            else:
                persona = form.save()
                rol = form.cleaned_data.get('tipo_usuario')
                ## estado_empleado = form.cleaned_data.get('estado')
                cargo = form.cleaned_data.get('cargo')
                # Si es gerente, asignar automaticamente el cargo de gerente del departamento
                if rol == 'gerente' and departamento_id:
                    cargo = Cargo.get_gerente_por_departamento(departamento_id)
                    if not cargo:
                        form.add_error('departamento', 'No hay un cargo de gerente configurado para este departamento.')
                        personas = Persona.objects.all()
                        return render(request, 'personas.html', {'form': form, 'personas': personas})
                # Definir estado_empleado según si es creacion o edicion
                if not id_persona:
                    estado_empleado = "activo"  # Estado fijo para creacion
                else:
                    estado_empleado = form.cleaned_data.get('estado')

                persona = form.save()

                # CREAR USUARIO SI ES NUEVA PERSONA
                if not id_persona:
                    # Generar username único: nombre.apellido / nombre.apellido1 / etc.
                    base_username = f"{persona.nombre}.{persona.apellido}".replace(" ", "").lower()
                    username = base_username
                    contador = 1
                    while Usuario.objects.filter(username=username).exists():
                        username = f"{base_username}{contador}"
                        contador += 1

                    password = persona.dni  # La contraseña es el DNI

                    # Crear usuario
                    usuario = Usuario.objects.create_user(
                        username=username,
                        password=password,
                        email=email,
                        persona=persona,
                        rol=rol
                    )

                    # Enviar email con credenciales
                    login_url = request.build_absolute_uri('/login/')
                    try:
                        send_mail(
                            subject="Credenciales de acceso",
                            message=f"Hola {persona.nombre},\n\n"
                                    f"Tu cuenta ha sido creada.\n"
                                    f"Usuario: {username}\n"
                                    f"Contraseña: {password}\n\n"
                                    f"Podés ingresar al sistema desde: {login_url}\n\n"
                                    f"Por favor, cambiá su contraseña luego de ingresar.\n\n"
                                    f"Saludos,\nEl equipo de RRHH",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print(f"Error al enviar el correo: {e}")

                else:
                    # Actualizar usuario si existe
                    try:
                        usuario = Usuario.objects.get(persona=persona)
                        usuario.email = form.cleaned_data.get('email')
                        usuario.rol = rol
                        usuario.save()
                    except Usuario.DoesNotExist:
                        print(f"Usuario no encontrado para persona {persona.id}")

                # Si es rol admin, le asignamos automáticamente el cargo "Administrador"
                if rol == 'admin':
                    try:
                        cargo = Cargo.objects.get(nombre="Administrador")
                    except Cargo.DoesNotExist:
                        cargo = None  # Si no existe, lo dejamos sin cargo y no se crea como empleado

                if rol in ['empleado', 'jefe', 'gerente', 'admin'] and cargo:
                    try:
                        empleado = Empleado.objects.get(id=persona.id)
                    except Empleado.DoesNotExist:
                        # Clonar la persona y convertirla en empleado
                        empleado = Empleado.objects.create(
                            id=persona.id,
                            nombre=persona.nombre,
                            apellido=persona.apellido,
                            dni=persona.dni,
                            telefono=persona.telefono,
                            prefijo_pais=persona.prefijo_pais,
                            fecha_nacimiento=persona.fecha_nacimiento,
                            fecha_ingreso=persona.fecha_ingreso,
                            pais=persona.pais,
                            provincia=persona.provincia,
                            ciudad=persona.ciudad,
                            calle=persona.calle,
                            numero=persona.numero,
                            genero=persona.genero,
                            avatar=persona.avatar,
                            cvitae=persona.cvitae,
                            fecha_creacion=persona.fecha_creacion,
                            fecha_actualizacion=persona.fecha_actualizacion,
                            estado=estado_empleado,
                            cargo=cargo,
                            cantidad_dias_disponibles=0
                        )
                    else:
                        # Actualizar si ya existía
                        empleado.estado = estado_empleado
                        if cargo:
                            empleado.cargo = cargo
                        empleado.save()

                    # Crear o actualizar historial de cargo
                    if cargo:
                        # Cerrar el último cargo activo, si existe
                        ultimo_cargo = EmpleadoCargo.objects.filter(
                            empleado=empleado,
                            fecha_fin__isnull=True
                        ).order_by('-fecha_inicio').first()

                        if ultimo_cargo and ultimo_cargo.cargo != cargo:
                            ultimo_cargo.fecha_fin = date.today()
                            ultimo_cargo.save()
                            try:
                                # Buscar el departamento anterior desde la relación CargoDepartamento
                                relacion_anterior = CargoDepartamento.objects.get(
                                    cargo=ultimo_cargo.cargo
                                )
                                relacion_anterior.vacante += 1
                                relacion_anterior.save()
                            except CargoDepartamento.DoesNotExist:
                                pass

                        # Registrar el nuevo cargo
                        EmpleadoCargo.objects.create(
                            empleado=empleado,
                            cargo=cargo,
                            fecha_inicio=date.today()
                        )
                        # Descontar vacante del nuevo cargo
                        try:
                            relacion_nueva = CargoDepartamento.objects.get(
                                cargo=cargo,
                                departamento=departamento_id
                            )
                            if relacion_nueva.vacante > 0:
                                relacion_nueva.vacante -= 1
                                relacion_nueva.save()
                        except CargoDepartamento.DoesNotExist:
                            pass
                else:
                    # Si pasa a rol normal, marcar como inactivo
                    try:
                        empleado = Empleado.objects.get(id=persona.id)
                        empleado.estado = 'inactivo'
                        empleado.save()
                    except Empleado.DoesNotExist:
                        pass

                return redirect('personas')
        else:
            print("Errores en el formulario:", form.errors)
    else:
        form = PersonaForm()

    personas = Persona.objects.all()
    return render(request, 'personas.html', {'form': form, 'personas': personas})


def cargos_por_departamento(request, dept_id):
    tipo_usuario = request.GET.get('tipo_usuario')

    relaciones = CargoDepartamento.objects.filter(departamento_id=dept_id).select_related('cargo')
    # Si se especifica tipo_usuario y es "jefe", filtramos los cargos con es_jefe=True
    if tipo_usuario == 'jefe':
        relaciones = relaciones.filter(cargo__es_jefe=True)
    elif tipo_usuario == 'gerente':  # Excluir cargos que sean gerente, ya que se asignan automáticamente
        relaciones = relaciones.exclude(cargo__es_gerente=True)
    elif tipo_usuario == 'empleado':
        relaciones = relaciones.exclude(cargo__es_jefe=True).exclude(cargo__es_gerente=True)

    cargos = []

    for r in relaciones:
        nombre = f"{r.cargo.nombre} ({r.vacante} vacantes)"
        cargos.append({
            'id': r.cargo.id,
            'nombre': nombre,
            'vacante': r.vacante
        })
    return JsonResponse({'cargos': cargos})


@require_POST
def eliminar_persona(request, persona_id):
    persona = get_object_or_404(Persona, id_persona=persona_id)
    persona.delete()
    return redirect('personas')
