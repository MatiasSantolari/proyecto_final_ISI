from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('home/', views.home, name='home'),
    
    path('profile/create/', views.create_persona, name='create_profile'),

    # Perfil usuario
    path('perfil/', views.perfil_usuario, name='user_perfil'),

# urlpatterns = [
#    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
 #   path('dashboard/empleado/', views.dashboard_empleado, name='dashboard_empleado'),
 #   path('dashboard/', views.dashboard_normal, name='dashboard_normal'),
 #   ]

     ## PERSONA ##
    path('personas/', views.personas, name='personas'),
    path('personas/crear/', views.crear_persona, name='crear_persona'),
    path('personas/<int:persona_id>/eliminar/', views.eliminar_persona, name='eliminar_persona'),
    ##path('personas/<int:persona_id>/datos/', views.obtener_datos_persona, name='obtener_datos_persona'),

    ## CARGO ##
    path('cargos/', views.cargos, name='cargos'),
    path('cargos/crear/', views.crear_cargo, name='crear_cargo'), ## Sirve para editar tambien
    path('cargos/<int:cargo_id>/eliminar/', views.eliminar_cargo, name='eliminar_cargo'),
    

## CATEGORIA del CARGO ##
    path('cargo_categoria/', views.cargos_categoria, name='cargo_categoria'),
    path('cargo_categoria/crear/', views.crear_cargo_categoria, name='crear_cargo_categoria'), ## Sirve para editar tambien
    path('cargo_categoria/<int:categoria_id>/eliminar/', views.eliminar_cargo_categoria, name='eliminar_cargo_categoria'),



    path('agregar_sueldo_base/', views.agregar_sueldo_base, name='agregar_sueldo_base'),
    path('beneficios/', views.beneficios, name='beneficios'),
    path('calcular_bonificaciones/', views.calcular_bonificaciones, name='calcular_bonificaciones'),
    path('capacitaciones/', views.capacitaciones, name='capacitaciones'),
    
    path('competencias/', views.competencias, name='competencias'),
    path('contratos/', views.contratos, name='contratos'),
    path('costos_de_personal/', views.costos_de_personal, name='costos_de_personal'),
    path('criterios_evaluacion/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('departamentos/', views.departamentos, name='departamentos'),
    path('empleados/', views.empleados, name='empleados'),
    path('evaluacion_desempeno/', views.evaluacion_desempeno, name='evaluacion_desempeno'),
    path('habilidades/', views.habilidades, name='habilidades'),



    path('instituciones/', views.instituciones, name='instituciones'),
    path('logros/', views.logros, name='logros'),
    path('nominas/', views.nominas, name='nominas'),
    path('objetivos/', views.objetivos, name='objetivos'),
   
    path('postulantes/', views.postulantes, name='postulantes'),
    path('publicar_ofertas_de_empleo/', views.publicar_ofertas_de_empleo, name='publicar_ofertas_de_empleo'),
    path('registrar_asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('solicitudes_nuevos_empleados/', views.solicitudes_nuevos_empleados, name='solicitudes_nuevos_empleados'),
    path('tipo_criterio_evaluacion/', views.tipo_criterio_evaluacion, name='tipo_criterio_evaluacion'),
    path('tipos_contrato/', views.tipos_contrato, name='tipos_contrato'),
    path('competencias_faltantes/', views.competencias_faltantes, name='competencias_faltantes'),
    path('costos_de_contratacion/', views.costos_de_contratacion, name='costos_de_contratacion'),
    path('reporte_evaluacion_desempeno/', views.reporte_evaluacion_desempeno, name='reporte_evaluacion_desempeno'),
    path('contratar_nuevo_empleado/', views.contratar_nuevo_empleado, name='contratar_nuevo_empleado'),
    path('ausencias_retardos/', views.ausencias_retardos, name='ausencias_retardos'),

]
