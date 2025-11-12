from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

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


@login_required
def personas(request):
    personas_qs = Persona.objects.select_related("empleado", "usuario").order_by(
        "apellido", "nombre"
    )

    departamentos = Departamento.objects.all()
    dep_id = request.GET.get("departamento")

    if dep_id:
        personas_qs = (
            personas_qs.filter(
                empleado__empleadocargo__fecha_fin__isnull=True,
                empleado__empleadocargo__cargo__cargodepartamento__departamento_id=dep_id,
            )
            .distinct()
        )

    personas_con_datos = []

    for persona in personas_qs:
        estado = ""
        cargo_id = ""
        nombre_cargo = ""
        tipo_usuario = ""
        departamento_id = ""
        departamento_nombre = ""

        if hasattr(persona, "usuario"):
            tipo_usuario = persona.usuario.rol

            if tipo_usuario in ["empleado", "jefe", "gerente", "admin"] and hasattr(
                persona, "empleado"
            ):
                estado = persona.empleado.estado

                ultimo_cargo = (
                    persona.empleado.empleadocargo_set.filter(fecha_fin__isnull=True).first()
                )
                if ultimo_cargo:
                    cargo = ultimo_cargo.cargo
                    cargo_id = cargo.id
                    nombre_cargo = cargo.nombre

                    cargo_departamento = CargoDepartamento.objects.filter(
                        cargo=cargo
                    ).first()
                    if cargo_departamento:
                        departamento_id = cargo_departamento.departamento.id
                        departamento_nombre = cargo_departamento.departamento.nombre
            else:
                estado = "Sin Estado"
                nombre_cargo = "Sin Cargo"

        personas_con_datos.append(
            {
                "id": persona.id,
                "nombre": persona.nombre,
                "apellido": persona.apellido,
                "dni": persona.dni,
                "email": persona.usuario.email,
                "prefijo_pais": persona.prefijo_pais,
                "telefono": persona.telefono,
                "fecha_nacimiento": persona.fecha_nacimiento,
                "genero": persona.genero,
                "pais": persona.pais,
                "provincia": persona.provincia,
                "ciudad": persona.ciudad,
                "calle": persona.calle,
                "numero": persona.numero,
                "tipo_usuario": tipo_usuario,
                "estado": estado,
                "cargo": cargo_id,
                "nombre_cargo": nombre_cargo,
                "departamento_id": departamento_id,
                "departamento_nombre": departamento_nombre,
                "telefono_completo": persona.prefijo_pais + persona.telefono,
            }
        )

    form = PersonaForm()
    return render(
        request,
        "personas/personas_list.html",
        {
            "personas": personas_con_datos,
            "form": form,
            "departamentos": departamentos,
            "departamento_seleccionado": dep_id,
        },
    )


@login_required
@require_POST
def crear_persona(request):
    if request.method == "POST":
        id_persona = request.POST.get("id_persona")
        persona = get_object_or_404(Persona, id=id_persona) if id_persona else None
        departamento_id = request.POST.get("departamento")

        form = PersonaForm(
            request.POST, request.FILES, instance=persona, departamento_id=departamento_id
        )

        if form.is_valid():
            email = form.cleaned_data.get("email")
            accion = request.POST.get("accion")

            if not id_persona and Usuario.objects.filter(email=email).exists():
                form.add_error(
                    "email", "Ya existe un usuario registrado con ese correo electrónico."
                )
            else:
                persona = form.save()
                rol = form.cleaned_data.get("tipo_usuario")
                cargo = form.cleaned_data.get("cargo")

                if rol == "gerente" and departamento_id:
                    cargo = Cargo.get_gerente_por_departamento(departamento_id)
                    if not cargo:
                        form.add_error(
                            "departamento",
                            "No hay un cargo de gerente configurado para este departamento.",
                        )
                        personas = Persona.objects.all()
                        return render(request, "personas/personas_list.html", {"form": form, "personas": personas})

                if (rol == "gerente" or rol == "jefe") and not cargo and departamento_id:
                    if rol == "gerente":
                        cargo = Cargo.get_gerente_por_departamento(departamento_id)
                    else:
                        cargo = Cargo.get_jefe_por_departamento(departamento_id)

                if not id_persona:
                    estado_empleado = "activo"
                else:
                    estado_empleado = form.cleaned_data.get("estado")

                persona = form.save()

                if not id_persona:
                    base_username = f"{persona.nombre}.{persona.apellido}".replace(" ", "").lower()
                    username = base_username
                    contador = 1
                    while Usuario.objects.filter(username=username).exists():
                        username = f"{base_username}{contador}"
                        contador += 1

                    password = persona.dni

                    usuario = Usuario.objects.create_user(
                        username=username,
                        password=password,
                        email=email,
                        persona=persona,
                        rol=rol,
                    )

                    if rol == "admin":
                        usuario.is_staff = True
                        usuario.is_superuser = True
                    else:
                        usuario.is_staff = False
                        usuario.is_superuser = False
                    usuario.save()

                    login_url = request.build_absolute_uri("/login/")
                    try:
                        send_mail(
                            subject="Credenciales de acceso",
                            message=(
                                f"Hola {persona.nombre},\n\n"
                                f"Tu cuenta ha sido creada.\n"
                                f"Usuario: {username}\n"
                                f"Contraseña: {password}\n\n"
                                f"Podés ingresar al sistema desde: {login_url}\n\n"
                                f"Por favor, cambie su contraseña luego de ingresar.\n\n"
                                f"Saludos,\nEl equipo de RRHH"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                    except Exception as e:  # pragma: no cover - logging side-effect
                        print(f"Error al enviar el correo: {e}")

                else:
                    try:
                        usuario = Usuario.objects.get(persona=persona)
                        usuario.email = form.cleaned_data.get("email")
                        usuario.rol = rol
                        if rol == "admin":
                            usuario.is_staff = True
                            usuario.is_superuser = True
                        else:
                            usuario.is_staff = False
                            usuario.is_superuser = False
                        usuario.save()

                    except Usuario.DoesNotExist:
                        print(f"Usuario no encontrado para persona {persona.id}")

                if rol == "admin":
                    try:
                        cargo = Cargo.objects.get(nombre="ADMIN")
                    except Cargo.DoesNotExist:
                        cargo = None

                if rol in ["empleado", "jefe", "gerente", "admin"] and cargo:
                    try:
                        empleado = Empleado.objects.get(id=persona.id)
                    except Empleado.DoesNotExist:
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
                            cantidad_dias_disponibles=0,
                        )
                    else:
                        empleado.estado = estado_empleado
                        if cargo:
                            empleado.cargo = cargo
                        empleado.save()

                    if cargo:
                        ultimo_cargo = (
                            EmpleadoCargo.objects.filter(
                                empleado=empleado, fecha_fin__isnull=True
                            )
                            .order_by("-fecha_inicio")
                            .first()
                        )

                        if not ultimo_cargo:
                            EmpleadoCargo.objects.create(
                                empleado=empleado, cargo=cargo, fecha_inicio=date.today()
                            )
                            try:
                                relacion_nueva = CargoDepartamento.objects.get(
                                    cargo=cargo, departamento=departamento_id
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
                                relacion_anterior = CargoDepartamento.objects.get(
                                    cargo=ultimo_cargo.cargo
                                )
                                relacion_anterior.vacante += 1
                                relacion_anterior.save()
                            except CargoDepartamento.DoesNotExist:
                                pass

                            EmpleadoCargo.objects.create(
                                empleado=empleado, cargo=cargo, fecha_inicio=date.today()
                            )
                            try:
                                relacion_nueva = CargoDepartamento.objects.get(
                                    cargo=cargo, departamento=departamento_id
                                )
                                if relacion_nueva.vacante > 0:
                                    relacion_nueva.vacante -= 1
                                    relacion_nueva.save()
                            except CargoDepartamento.DoesNotExist:
                                pass

                else:
                    try:
                        empleado = Empleado.objects.get(id=persona.id)
                        empleado.estado = "inactivo"
                        empleado.save()
                    except Empleado.DoesNotExist:
                        pass

                if accion == "guardar_crear_contrato":
                    tiene_activo = HistorialContrato.objects.filter(
                        empleado=persona.id, estado="activo"
                    ).exists()

                    if tiene_activo:
                        messages.warning(request, "La persona ya tiene un contrato activo.")
                        return redirect("contratos")
                    else:
                        return redirect(
                            f"/contratos/?crear_contrato=1&empleado_id={empleado.id}"
                        )

                return redirect("personas")
        else:
            print("Errores en el formulario:", form.errors)
    else:
        form = PersonaForm()

    personas = Persona.objects.all()
    return render(request, "personas/personas_list.html", {"form": form, "personas": personas})


@login_required
def cargos_por_departamento(request, dept_id):
    tipo_usuario = request.GET.get("tipo_usuario")

    relaciones = CargoDepartamento.objects.filter(
        departamento_id=dept_id
    ).select_related("cargo")
    if tipo_usuario == "jefe":
        relaciones = relaciones.filter(cargo__es_jefe=True)
    elif tipo_usuario == "gerente":
        relaciones = relaciones.exclude(cargo__es_gerente=True)
    elif tipo_usuario == "empleado":
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
@require_POST
def eliminar_persona(request, persona_id):
    persona = get_object_or_404(Persona, id_persona=persona_id)
    persona.delete()
    return redirect("personas")


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
