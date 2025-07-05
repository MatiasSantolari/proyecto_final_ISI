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
    

@login_required
def create_persona(request):
    if request.method == 'POST':
        form = PersonaFormCreate(request.POST, request.FILES)
        if form.is_valid():
            persona = form.save(commit=False)

            prefijo = form.cleaned_data.get('prefijo_pais')
            numero = form.cleaned_data.get('numero_telefono')
            persona.telefono = f"{prefijo}{numero}" if prefijo and numero else ''

            persona.save()

            user = request.user
            user.persona = persona
            user.save()

            return redirect('home')
    else:
        form = PersonaFormCreate()

    return render(request, 'auth/create_profile.html', {'form': form})



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


##########################


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

        print(f"Cargo: {cargo.nombre}, Categoria: {cargo.categoria}, ID: {cargo.categoria.id_categoria}")
        
        cargos_con_sueldo.append({
            'id': cargo.id_cargo,
            'nombre': cargo.nombre,
            'descripcion': cargo.descripcion,
            'sueldo_base': sueldo,
            'categoria': cargo.categoria,
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
        print(f"Cargo: {cargo.nombre}, Categoria: {cargo.categoria}, ID: {cargo.categoria.id_categoria}")
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
        form = CargoForm(instance=cargo)
    cargos = Cargo.objects.all()

    return render(request, 'cargos.html', {'form': form, 'cargos': cargos})


@require_POST
def eliminar_cargo(request, cargo_id):
    cargo = get_object_or_404(Cargo, id_cargo=cargo_id)
    cargo.delete()
    return redirect('cargos')



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
def eliminar_cargo_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaCargo, id_categoria=categoria_id)
    categoria.delete()
    return redirect('cargo_categoria')





def cargo_categoria(request): return render(request, 'cargo_categoria.html')
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
