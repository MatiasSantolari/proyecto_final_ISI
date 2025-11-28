from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.utils.datatables import get_datatable_context
from personas import datatables_registry
from core.constants import ROL_USUARIO_CHOICES
from .services import generar_usuario

from core.models import (
    Cargo,
    CargoDepartamento,
    Certificacion,
    DatoAcademico,
    Departamento,
    Empleado,
    EmpleadoCargo,
    ExperienciaLaboral,
    HistorialContrato,
    Persona,
    Usuario,
)
from personas.forms import (
    CertificacionForm,
    DatoAcademicoForm,
    ExperienciaLaboralForm,
    PersonaForm,
)


def _personas_context(request, form=None):
    departamentos = Departamento.objects.all()
    departamento = request.GET.get("departamento")

    tipos_usuarios = ROL_USUARIO_CHOICES
    tipo_usuario = request.GET.get("tipo_usuario")

    if form is None:
        form = PersonaForm()

    datatable_definition = get_datatable_context("personas")

    #BUSCO PERSONAS
    personas = Persona.objects.all().order_by("apellido", "nombre")
    if departamento not in ('0', None):
        personas = personas.filter(
            empleado__empleadocargo__fecha_fin__isnull=True,
            empleado__empleadocargo__cargo__cargodepartamento__departamento_id=departamento,
        )
    if tipo_usuario not in ('0', None):
        personas = personas.filter(usuario__rol=tipo_usuario)

    return {
        "personas": personas,
        "form": form,
        "departamentos": departamentos,
        "departamento_seleccionado": departamento,
        "tipos_usuarios": tipos_usuarios,
        "tipo_usuario_seleccionado": tipo_usuario,
        "datatable": datatable_definition,
    }


@login_required
def personas(request):
    context = _personas_context(request)
    return render(request, "personas/personas_list.html", context)


@login_required
def crear_persona(request):
    if request.method == "POST":
        return _guardar_persona(request)

    context = _personas_context(request, form=PersonaForm())
    context["mostrar_modal_persona"] = True
    return render(request, "personas/personas_list.html", context)


@login_required
def editar_persona(request):
    if request.method == "POST":
        persona_id = request.POST.get("id_persona")
        persona_instance = get_object_or_404(Persona, id=persona_id)
        return _guardar_persona(request, persona_instance)

    persona_id = request.GET.get("id_persona")
    persona_instance = get_object_or_404(Persona, id=persona_id)
    form = PersonaForm(instance=persona_instance)
    context = _personas_context(request, form=form)
    context["mostrar_modal_persona"] = True
    return render(request, "personas/personas_list.html", context)


def _guardar_persona(request, persona_instance=None):
    form = PersonaForm(request.POST, instance=persona_instance)

    #Valido el form
    if not form.is_valid():
        context = _personas_context(request, form=form)
        context["mostrar_modal_persona"] = True
        return render(request, "personas/personas_list.html", context, status=400)
    
    #Valido el email
    email = form.cleaned_data.get('email')
    usuario_existente_qs = Usuario.objects.filter(email=email)
    if persona_instance:
        usuario_existente_qs = usuario_existente_qs.exclude(
            id_usuario=persona_instance.usuario.id_usuario
        )
    if usuario_existente_qs.exists():
        form.add_error('email', 'Ya existe un usuario registrado con ese correo electrónico.')
        context = _personas_context(request, form=form)
        context["mostrar_modal_persona"] = True
        return render(request, "personas/personas_list.html", context, status=400)
    
    persona = form.save() #Guardo Persona
    
    #Genero/Actualizo Usuario
    rol = form.cleaned_data.get('tipo_usuario')
    if persona_instance:
        estado_empleado = form.cleaned_data.get('estado')
        usuario = getattr(persona, "usuario")
        if usuario:
            usuario.email = email
            usuario.rol = rol
            es_admin = rol == "5"
            usuario.is_staff = es_admin
            usuario.is_superuser = es_admin
            usuario.save()
        else:
            generar_usuario(persona, email, rol, request.build_absolute_uri('/login/'))
    else:
        estado_empleado = 1
    #CEPARTAMENTO Y CARGO -> PARA GENERAR EMPLEADO
    departamento = form.cleaned_data.get('departamento')
    cargo = form.cleaned_data.get('cargo')
    if persona_instance:
        empleado = Empleado.objects.filter(id=persona.id).first()
    if rol in ['5', '4', '3', '2'] and departamento:
        #if not cargo:
            # Tengo que seleccionar el cargo con el departamento y el rol del usuario
        if not empleado:
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
            empleado.save()
        else:
            empleado.estado = estado_empleado
            empleado.cargo = cargo
            empleado.save()

    if cargo and empleado:
        ultimo_cargo = EmpleadoCargo.objects.filter(empleado=empleado, fecha_fin__isnull=True).order_by('-fecha_inicio').first()

        if not ultimo_cargo:
            EmpleadoCargo.objects.create(
                empleado=empleado,
                cargo=cargo,
                fecha_inicio=date.today()
            )
            try:
                relacion_nueva = CargoDepartamento.objects.get(
                    cargo=cargo,
                    departamento=departamento
                )
                if relacion_nueva.vacante > 0:
                    relacion_nueva.vacante -= 1
                    relacion_nueva.save()
            except CargoDepartamento.DoesNotExist:
                pass
    

        elif ultimo_cargo.cargo != cargo:
            ultimo_cargo.fecha_fin = date.today()
            ultimo_cargo.save()
            try:
                relacion_anterior = CargoDepartamento.objects.get(cargo=ultimo_cargo.cargo)
                relacion_anterior.vacante += 1
                relacion_anterior.save()
            except CargoDepartamento.DoesNotExist:
                pass

            EmpleadoCargo.objects.create(
                empleado=empleado,
                cargo=cargo,
                fecha_inicio=date.today()
            )
            try:
                relacion_nueva = CargoDepartamento.objects.get(
                    cargo=cargo,
                    departamento=departamento
                )
                if relacion_nueva.vacante > 0:
                    relacion_nueva.vacante -= 1
                    relacion_nueva.save()
            except CargoDepartamento.DoesNotExist:
                pass

        else:
            pass

    else:
        try:
            empleado = Empleado.objects.get(id=persona.id)
            empleado.estado = 'inactivo'
            empleado.save()
        except Empleado.DoesNotExist:
            pass

    #ACCION
    accion = request.POST.get("accion")
    if accion == "guardar_crear_contrato" and empleado:
        tiene_activo = HistorialContrato.objects.filter(
            empleado=persona.id, estado="activo"
        ).exists()

        if tiene_activo:
            messages.warning(request, "La persona ya tiene un contrato activo.")
            return redirect("contratos")
        else:
            return redirect(f"/contratos/?crear_contrato=1&empleado_id={empleado.id}")

    form.save()
    messages.success(request, "Persona creada correctamente." if not persona_instance else "Persona actualizada correctamente.")
    return redirect("personas")


@login_required
@require_POST
def eliminar_persona(request, persona_id):
    persona = get_object_or_404(Persona, id_persona=persona_id)
    persona.delete()
    return redirect("personas")

@login_required
def cargos_por_departamento(request, departamento_id):
    relaciones = CargoDepartamento.objects.filter(
        departamento_id=departamento_id
    ).select_related("cargo")
    relaciones = relaciones.exclude(cargo__es_jefe=True).exclude(cargo__es_gerente=True)

    cargos = []

    for relacion in relaciones:
        nombre = f"{relacion.cargo.nombre} ({relacion.vacante} vacantes)"
        cargos.append(
            {
                "id": relacion.cargo.id,
                "nombre": nombre,
                "vacante": relacion.vacante,
            }
        )
    return JsonResponse({"cargos": cargos})

@login_required
def departamentos_por_tipoUsuario(request, tipo_usuario):
    if tipo_usuario == 2:
        relaciones = (
            CargoDepartamento.objects.filter(vacante__gt=0)
            .select_related("departamento")
            .exclude(cargo__es_jefe=True)
            .exclude(cargo__es_gerente=True)
        )
        departamentos = relaciones
    elif tipo_usuario == 3:
        departamentos = CargoDepartamento.objects.filter(
            cargo__es_jefe=True, vacante__gt=0
        ).select_related("departamento")
    elif tipo_usuario == 4:
        departamentos = CargoDepartamento.objects.filter(
            cargo__es_gerente=True, vacante__gt=0
        ).select_related("departamento")
    else:
        departamentos = CargoDepartamento.objects.none()

    dates = []

    for departamento in departamentos:
        dates.append(
            {
                "id": departamento.departamento.id,
                "nombre": departamento.departamento.nombre,
            }
        )
    return JsonResponse({"departamentos": dates})


@login_required
def datos_academicos_list(request):
    persona = request.user.persona
    datos = persona.datos_academicos.all()
    data = [
        {
            "id": dato.id,
            "carrera": dato.carrera,
            "institucion": dato.institucion,
            "situacion_academica": dato.situacion_academica,
            "fecha_inicio": dato.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": dato.fecha_fin.strftime("%Y-%m-%d") if dato.fecha_fin else "",
        }
        for dato in datos
    ]
    return JsonResponse({"datos": data})


@login_required
@csrf_exempt
def datos_academicos_save(request):
    if request.method == "POST":
        data = request.POST
        persona = request.user.persona
        dato_id = data.get("id")

        if dato_id:
            dato = DatoAcademico.objects.get(id=dato_id, persona=persona)
            form = DatoAcademicoForm(data, instance=dato)
        else:
            form = DatoAcademicoForm(data)

        if form.is_valid():
            nuevo_dato = form.save(commit=False)
            nuevo_dato.persona = persona
            nuevo_dato.save()
            return JsonResponse({"success": True, "id": nuevo_dato.id})
        else:
            return JsonResponse({"success": False, "errors": form.errors})


@login_required
@csrf_exempt
def datos_academicos_delete(request):
    if request.method == "POST":
        dato_id = request.POST.get("id")
        persona = request.user.persona
        try:
            dato = DatoAcademico.objects.get(id=dato_id, persona=persona)
            dato.delete()
            return JsonResponse({"success": True})
        except DatoAcademico.DoesNotExist:
            return JsonResponse({"success": False, "error": "Dato no encontrado"})


@login_required
def certificaciones_list(request):
    persona = request.user.persona
    datos = persona.certificaciones.all()
    data = [
        {
            "id": certificacion.id,
            "nombre": certificacion.nombre,
            "institucion": certificacion.institucion,
            "fecha_inicio": certificacion.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": certificacion.fecha_fin.strftime("%Y-%m-%d")
            if certificacion.fecha_fin
            else "",
        }
        for certificacion in datos
    ]
    return JsonResponse({"datos": data})


@login_required
@csrf_exempt
def certificaciones_save(request):
    if request.method == "POST":
        data = request.POST
        persona = request.user.persona
        dato_id = data.get("id")

        if dato_id:
            dato = Certificacion.objects.get(id=dato_id, persona=persona)
            form = CertificacionForm(data, instance=dato)
        else:
            form = CertificacionForm(data)

        if form.is_valid():
            nuevo_dato = form.save(commit=False)
            nuevo_dato.persona = persona
            nuevo_dato.save()
            return JsonResponse({"success": True, "id": nuevo_dato.id})
        else:
            return JsonResponse({"success": False, "errors": form.errors})


@login_required
@csrf_exempt
def certificaciones_delete(request):
    if request.method == "POST":
        dato_id = request.POST.get("id")
        persona = request.user.persona
        try:
            dato = Certificacion.objects.get(id=dato_id, persona=persona)
            dato.delete()
            return JsonResponse({"success": True})
        except Certificacion.DoesNotExist:
            return JsonResponse({"success": False, "error": "Certificación no encontrada"})


@login_required
def experiencias_list(request):
    persona = request.user.persona
    datos = persona.experiencias.all().order_by("-fecha_inicio")
    data = [
        {
            "id": experiencia.id,
            "cargo_exp": experiencia.cargo_exp,
            "empresa": experiencia.empresa,
            "descripcion": experiencia.descripcion or "",
            "fecha_inicio": experiencia.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_fin": experiencia.fecha_fin.strftime("%Y-%m-%d")
            if experiencia.fecha_fin
            else "",
            "actualidad": experiencia.actualidad,
        }
        for experiencia in datos
    ]
    return JsonResponse({"datos": data})


@login_required
@csrf_exempt
def experiencias_save(request):
    if request.method == "POST":
        data = request.POST
        persona = request.user.persona
        exp_id = data.get("id")

        if exp_id:
            exp = ExperienciaLaboral.objects.get(id=exp_id, persona=persona)
            form = ExperienciaLaboralForm(data, instance=exp)
        else:
            form = ExperienciaLaboralForm(data)

        if form.is_valid():
            nueva_exp = form.save(commit=False)
            nueva_exp.persona = persona
            nueva_exp.save()
            return JsonResponse({"success": True, "id": nueva_exp.id})
        else:
            return JsonResponse({"success": False, "errors": form.errors})


@login_required
@csrf_exempt
def experiencias_delete(request):
    if request.method == "POST":
        exp_id = request.POST.get("id")
        persona = request.user.persona
        try:
            exp = ExperienciaLaboral.objects.get(id=exp_id, persona=persona)
            exp.delete()
            return JsonResponse({"success": True})
        except ExperienciaLaboral.DoesNotExist:
            return JsonResponse({"success": False, "error": "Experiencia no encontrada"})
