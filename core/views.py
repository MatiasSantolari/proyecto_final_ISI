from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .models import *
from .forms import *
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
from .decorators import rol_requerido
from django.utils.timezone import now


# test
# def myview(request):
#    data = {
#        'name': 'pepe',
#        'empleados': Empleado.objects.all()
#    }
#    return render(request, 'home.html', data)

"""
@login_required
@rol_requerido('admin', 'gerente')
def dashboard_admin(request):
    return render(request, 'core/dashboard_admin.html')

@login_required
@rol_requerido('empleado')
def dashboard_empleado(request):
    return render(request, 'core/dashboard_empleado.html')

@login_required
def dashboard_normal(request):
    return render(request, 'core/dashboard_normal.html')
"""

@login_required
def home(request):
    user = request.user
    rol = user.rol
    if not user.persona:
        return redirect('create_profile')
    else:
        if rol == 'admin':
            return render(request, 'index.html')
        elif rol == 'gerente':
            return render(request, 'index.html')
        elif rol == 'empleado':
            return render(request, 'index.html')
        else:
            return render(request, 'index.html')
    

def registrar_usuario(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente. Iniciá sesión.")
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'auth/register.html', {'form': form})


@login_required
def create_persona(request):
    if request.method == 'POST':
        form = PersonaFormCreate(request.POST, request.FILES)
        if form.is_valid():
            persona = form.save(commit=False)

            persona.save()

            user = request.user
            user.persona = persona
            user.save()

            return redirect('home')
    else:
        form = PersonaFormCreate()

    return render(request, 'auth/create_profile.html', {'form': form})


@login_required
def perfil_usuario(request):
    persona = request.user.persona

    form = PersonaFormCreate(
        request.POST or None,
        request.FILES or None,
        instance=persona,
        initial={
            'fecha_nacimiento': persona.fecha_nacimiento.strftime('%Y-%m-%d') if persona.fecha_nacimiento else ''
        }
    )

    if request.method == 'POST' and form.is_valid():
        # Si el usuario solicitó eliminar el CV
        if request.POST.get('eliminar_cvitae') == '1':
            if persona.cvitae:
                if persona.cvitae.storage.exists(persona.cvitae.name):
                    persona.cvitae.delete(save=False)
                persona.cvitae = None

        form.save()
        return redirect('user_perfil')

    return render(request, 'user_perfil.html', {'form': form})


##########################


################## CRUD PERSONA ################
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
                        EmpleadoCargo.objects.update_or_create(
                            empleado=empleado,
                            defaults={
                                'cargo': cargo,
                                'fecha_inicio': date.today()
                            }
                        )
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
    elif tipo_usuario == 'gerente':     # Excluir cargos que sean gerente, ya que se asignan automáticamente
        relaciones = relaciones.exclude(cargo__es_gerente=True)
    elif tipo_usuario == 'empleado':
        relaciones = relaciones.exclude(cargo__es_jefe=True).exclude(cargo__es_gerente=True)

    cargos = [{'id': r.cargo.id, 'nombre': r.cargo.nombre} for r in relaciones]
    return JsonResponse({'cargos': cargos})



@require_POST
def eliminar_persona(request, persona_id):
    persona = get_object_or_404(Persona, id_persona=persona_id)
    persona.delete()
    return redirect('personas')




########## CRUD CARGO #################

def cargos(request):
    cargos_con_sueldo = []

    relaciones = CargoDepartamento.objects.select_related('cargo', 'departamento')

    for relacion in relaciones:
        cargo = relacion.cargo
        departamento = relacion.departamento

        # Sueldo base (último)
        ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo).order_by('-fecha_sueldo').first()
        sueldo = ultimo_sueldo.sueldo_base if ultimo_sueldo else None

        cargos_con_sueldo.append({
            'id': cargo.id,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
            'departamento_id': departamento.id,
            'departamento': departamento.nombre,
            'vacante': relacion.vacante
        })

    form = CargoForm()
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

            departamento = form.cleaned_data['departamento']
            vacante = form.cleaned_data['vacante']

            # Crear o actualizar la relación intermedia CargoDepartamento
            CargoDepartamento.objects.update_or_create(
                cargo=cargo_guardado,
                departamento=departamento,
                defaults={'vacante': vacante}
            )

            # Registrar sueldo si cambió
            ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo_guardado).order_by('-fecha_sueldo').first()
            if not ultimo_sueldo or ultimo_sueldo.sueldo_base != sueldo_base:
                HistorialSueldoBase.objects.create(
                    cargo=cargo_guardado,
                    sueldo_base=sueldo_base,
                    fecha_sueldo=timezone.now()
                )

            return redirect('cargos')
    else:
        form = CargoForm(instance=cargo)

    # Listado para mostrar en el HTML
    cargos_con_sueldo = []
    cargos = Cargo.objects.all()

    for cargo in cargos:
        cargo_departamento = CargoDepartamento.objects.filter(cargo=cargo).first()
        departamento = cargo_departamento.departamento.nombre if cargo_departamento else 'Sin asignar'
        vacante = cargo_departamento.vacante if cargo_departamento else 0

        ultimo_sueldo = HistorialSueldoBase.objects.filter(cargo=cargo).order_by('-fecha_sueldo').first()
        sueldo = ultimo_sueldo.sueldo_base if ultimo_sueldo else None

        cargos_con_sueldo.append({
            'id': cargo.id,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
            'departamento': departamento,
            'vacante': vacante
        })

    return render(request, 'cargos.html', {'form': form, 'cargos': cargos_con_sueldo})



@require_POST
def eliminar_cargo(request, id_cargo):
    cargo = get_object_or_404(Cargo, id=id_cargo)
    cargo.delete()
    return redirect('cargos')

################

######CRUD Departamentos #####################
def departamentos(request): return render(request, 'departamentos.html')


# Al crear un departamento debria crearse los cargos:
#Cargo.objects.create(nombre='Jefe', departamento=departamento, es_jefe=True)
#Cargo.objects.create(nombre='Sub-jefe', departamento=departamento, es_jefe=True)
#Cargo.objects.create(nombre='Encargado', departamento=departamento, es_jefe=True)
#################


def cargo_categoria(request): return render(request, 'cargo_categoria.html')
def agregar_sueldo_base(request): return render(request, 'agregar_sueldo_base.html')
def beneficios(request): return render(request, 'beneficios.html')
def calcular_bonificaciones(request): return render(request, 'calcular_bonificaciones.html')
def capacitaciones(request): return render(request, 'capacitaciones.html')
def competencias(request): return render(request, 'competencias.html')
def contratos(request): return render(request, 'contratos.html')
def costos_de_personal(request): return render(request, 'costos_de_personal.html')
def criterios_evaluacion(request): return render(request, 'criterios_evaluacion.html')
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








"""
########## CRUD CATEGORIA CARGO #################
def cargos_categoria(request):
    categorias = CategoriaCargo.objects.all()
    form = CategoriaCargoForm()
    return render(request, 'cargo_categoria.html', {'categorias': categorias, 'form': form}) 


def crear_cargo_categoria(request):
    if request.method == 'POST':
        id_categoria = request.POST.get('id_categoria')
        
        if id_categoria:
            categoria = get_object_or_404(CategoriaCargo, pk=id_categoria)
            form = CategoriaCargoForm(request.POST, instance=categoria)
        else:
            form = CategoriaCargoForm(request.POST)
            
        if form.is_valid():
            form.save()
            return redirect('cargo_categoria')
        
    categorias = CategoriaCargo.objects.all()

    return render(request, 'cargo_categoria.html', {'form': form, 'categorias': categorias})


@require_POST
def eliminar_cargo_categoria(request, id_categoria):
    categoria = get_object_or_404(CategoriaCargo, id=id_categoria)
    categoria.delete()
    return redirect('cargo_categoria')
"""





"""
def obtener_datos_persona(request, persona_id):
    try:
        persona = Persona.objects.get(id_persona=persona_id)
        data = {
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'dni': persona.dni,
            'email': persona.usuario.email,
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
"""
