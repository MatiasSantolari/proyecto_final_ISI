from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('home/', views.home, name='home'),
    
     path('cambiar_vista/', views.cambiar_vista, name='cambiar_vista'),
     
    path('profile/create/', views.create_persona, name='create_profile'),

    # Perfil usuario
    path('perfil/', views.perfil_usuario, name='user_perfil'),
    path('actualizar-cv/', views.actualizar_cv_ajax, name='actualizar_cv_ajax'),


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

    path('personas/cargos_por_departamento/<int:dept_id>/', views.cargos_por_departamento, name='cargos_por_departamento'),

    ## CARGO ##
    path('cargos/', views.cargos, name='cargos'),
    path('cargos/crear/', views.crear_cargo, name='crear_cargo'), ## Sirve para editar tambien
    path('cargos/<int:id_cargo>/eliminar/', views.eliminar_cargo, name='eliminar_cargo'),
    

    ## DEPARTAMENTO ##
    path('departamentos/', views.departamentos, name='departamentos'),
    path('departamentos/crear/', views.crear_departamento, name='crear_departamento'),
    path('departamentos/<int:id_departamento>/eliminar/', views.eliminar_departamento, name='eliminar_departamento'),

    ## SOLICITUDES ##
    path('ofertas/', views.listar_ofertas, name='ofertas_empleo'),
    path('postularse/<int:cargo_id>/', views.postularse_a_cargo, name='postularse'),
    path('postulaciones/', views.ver_postulaciones_admin, name='admin_postulaciones'),
    path('postulaciones/cambiar_estado/', views.cambiar_estado_solicitud, name='cambiar_estado_solicitud'),
    path('postulaciones/finalizar/', views.finalizar_postulaciones_cargo, name='finalizar_postulaciones'),
    path('habilitar_cargo/', views.habilitar_cargo_para_postulaciones, name='habilitar_cargo'),
    path('limpiar_postulantes/', views.limpiar_postulantes_cargo, name='limpiar_postulantes'),


    ## OBJETIVOS ##
    path('objetivos/', views.objetivos, name='objetivos'),
    path('objetivos/crear/', views.crear_objetivo, name='crear_objetivo'),
    path('objetivos/<int:id_objetivo>/desactivar/', views.desactivar_objetivo, name='desactivar_objetivo'),
    path('objetivos/<int:id_objetivo>/eliminar/', views.eliminar_objetivo, name='eliminar_objetivo'),
    path('objetivos/<int:id_objetivo>/activar/', views.activar_objetivo, name='activar_objetivo'),
    path('objetivos/obtener_datos_asignacion/', views.obtener_datos_asignacion, name='obtener_datos_asignacion'),
    path('objetivos/asignar/', views.asignar_objetivo, name='asignar_objetivo'),
    path('objetivos/marcar-objetivo/', views.marcar_objetivo, name='marcar_objetivo'),
##  path('objetivos/obtener_asignaciones_objetivo/', views.obtener_asignaciones_objetivo, name='obtener_asignaciones_objetivo'),


    ## BENEFICIOS ##
    path('beneficios/', views.beneficios, name='beneficios'),
    path('beneficios/crear/', views.crear_beneficio, name='crear_beneficio'),
    path('beneficios/<int:id_beneficio>/desactivar/', views.desactivar_beneficio, name='desactivar_beneficio'),
    path('beneficios/<int:id_beneficio>/activar/', views.activar_beneficio, name='activar_beneficio'),
    path('beneficios/<int:id_beneficio>/eliminar/', views.eliminar_beneficio, name='eliminar_beneficio'),


    ## DESCUENTOS ##
    path('descuentos/', views.descuentos, name='descuentos'),
    path('descuentos/crear/', views.crear_descuento, name='crear_descuento'),
    path('descuentos/<int:id_descuento>/desactivar/', views.desactivar_descuento, name='desactivar_descuento'),
    path('descuentos/<int:id_descuento>/activar/', views.activar_descuento, name='activar_descuento'),
    path('descuentos/<int:id_descuento>/eliminar/', views.eliminar_descuento, name='eliminar_descuento'),



##############################################

    path('agregar_sueldo_base/', views.agregar_sueldo_base, name='agregar_sueldo_base'),
    path('calcular_bonificaciones/', views.calcular_bonificaciones, name='calcular_bonificaciones'),
    path('capacitaciones/', views.capacitaciones, name='capacitaciones'),
    
    path('competencias/', views.competencias, name='competencias'),
    path('contratos/', views.contratos, name='contratos'),
    path('costos_de_personal/', views.costos_de_personal, name='costos_de_personal'),
    path('criterios_evaluacion/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('evaluacion_desempeno/', views.evaluacion_desempeno, name='evaluacion_desempeno'),
    path('habilidades/', views.habilidades, name='habilidades'),


    path('instituciones/', views.instituciones, name='instituciones'),
    path('logros/', views.logros, name='logros'),
    path('nominas/', views.nominas, name='nominas'),
   
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
