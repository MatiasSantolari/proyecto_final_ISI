from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import *

from core import views 

urlpatterns = [
    path('home/', login_view.home, name='home'),
    
    path('cambiar_vista/', login_view.cambiar_vista, name='cambiar_vista'),
     
    path('profile/create/', login_view.create_persona, name='create_profile'),

    # Perfil usuario
    path('perfil/', login_view.perfil_usuario, name='user_perfil'),
    path('actualizar-cv/', postulaciones_view.actualizar_cv_ajax, name='actualizar_cv_ajax'),


# urlpatterns = [
#    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
 #   path('dashboard/empleado/', views.dashboard_empleado, name='dashboard_empleado'),
 #   path('dashboard/', views.dashboard_normal, name='dashboard_normal'),
 #   ]

     ## PERSONA ##
    path('personas/', personas_view.personas, name='personas'),
    path('personas/crear/', personas_view.crear_persona, name='crear_persona'),
    path('personas/<int:persona_id>/eliminar/', personas_view.eliminar_persona, name='eliminar_persona'),
    ##path('personas/<int:persona_id>/datos/', personas_view.obtener_datos_persona, name='obtener_datos_persona'),

    path('personas/cargos_por_departamento/<int:dept_id>/', personas_view.cargos_por_departamento, name='cargos_por_departamento'),

    ## CARGO ##
    path('cargos/', cargos_view.cargos, name='cargos'),
    path('cargos/crear/', cargos_view.crear_cargo, name='crear_cargo'), ## Sirve para editar tambien
    path('cargos/<int:id_cargo>/eliminar/', cargos_view.eliminar_cargo, name='eliminar_cargo'),
    

    ## DEPARTAMENTO ##
    path('departamentos/', departamentos_view.departamentos, name='departamentos'),
    path('departamentos/crear/', departamentos_view.crear_departamento, name='crear_departamento'),
    path('departamentos/<int:id_departamento>/eliminar/', departamentos_view.eliminar_departamento, name='eliminar_departamento'),


      ## HABILIDAD ##
    path('habilidades/', habilidades_view.habilidades, name='habilidades'),
    path('habilidades/crear/', habilidades_view.crear_habilidad, name='crear_habilidad'),
    path('habilidades/<int:id_habilidad>/eliminar/', habilidades_view.eliminar_habilidad, name='eliminar_habilidad'),


    ## POSTULACIONES ##
    path('ofertas/', postulaciones_view.listar_ofertas, name='ofertas_empleo'),
    path('postularse/<int:cargo_id>/', postulaciones_view.postularse_a_cargo, name='postularse'),
    path('postulaciones/', postulaciones_view.ver_postulaciones_admin, name='admin_postulaciones'),
    path('postulaciones/cambiar_estado/', postulaciones_view.cambiar_estado_solicitud, name='cambiar_estado_solicitud'),
    path('postulaciones/finalizar/', postulaciones_view.finalizar_postulaciones_cargo, name='finalizar_postulaciones'),
    path('habilitar_cargo/', postulaciones_view.habilitar_cargo_para_postulaciones, name='habilitar_cargo'),
    path('limpiar_postulantes/', postulaciones_view.limpiar_postulantes_cargo, name='limpiar_postulantes'),


    ## OBJETIVOS ##
    path('objetivos/', objetivos_view.objetivos, name='objetivos'),
    path('objetivos/crear/', objetivos_view.crear_objetivo, name='crear_objetivo'),
    path('objetivos/<int:id_objetivo>/desactivar/', objetivos_view.desactivar_objetivo, name='desactivar_objetivo'),
    path('objetivos/<int:id_objetivo>/eliminar/', objetivos_view.eliminar_objetivo, name='eliminar_objetivo'),
    path('objetivos/<int:id_objetivo>/activar/', objetivos_view.activar_objetivo, name='activar_objetivo'),
    path('objetivos/obtener_datos_asignacion/', objetivos_view.obtener_datos_asignacion, name='obtener_datos_asignacion'),
    path('objetivos/asignar/', objetivos_view.asignar_objetivo, name='asignar_objetivo'),
    path('objetivos/marcar-objetivo/', objetivos_view.marcar_objetivo, name='marcar_objetivo'),
##  path('objetivos/obtener_asignaciones_objetivo/', objetivos_view.obtener_asignaciones_objetivo, name='obtener_asignaciones_objetivo'),


    ## BENEFICIOS ##
    path('beneficios/', beneficios_view.beneficios, name='beneficios'),
    path('beneficios/crear/', beneficios_view.crear_beneficio, name='crear_beneficio'),
    path('beneficios/<int:id_beneficio>/desactivar/', beneficios_view.desactivar_beneficio, name='desactivar_beneficio'),
    path('beneficios/<int:id_beneficio>/activar/', beneficios_view.activar_beneficio, name='activar_beneficio'),
    path('beneficios/<int:id_beneficio>/eliminar/', beneficios_view.eliminar_beneficio, name='eliminar_beneficio'),


    ## DESCUENTOS ##
    path('descuentos/', descuentos_view.descuentos, name='descuentos'),
    path('descuentos/crear/', descuentos_view.crear_descuento, name='crear_descuento'),
    path('descuentos/<int:id_descuento>/desactivar/', descuentos_view.desactivar_descuento, name='desactivar_descuento'),
    path('descuentos/<int:id_descuento>/activar/', descuentos_view.activar_descuento, name='activar_descuento'),
    path('descuentos/<int:id_descuento>/eliminar/', descuentos_view.eliminar_descuento, name='eliminar_descuento'),


    ## NOMINAS ##
    path('nominas/', nominas_view.nominas, name='nominas'),
    path('nominas/editar/', nominas_view.editar_nomina, name='editar_nomina'),
    path('nominas/ver/<int:id_nomina>/', nominas_view.ver_nomina, name='ver_nomina'),
    path('nominas/anular/<int:id_nomina>/', nominas_view.anular_nomina, name='anular_nomina'),
    path('nominas/eliminar/<int:id_nomina>/', nominas_view.eliminar_nomina, name='eliminar_nomina'),
    path('nominas/generar/', nominas_view.generar_nominas, name='generar_nominas'),
    path('nominas/confirmar/', nominas_view.confirmar_nominas, name='confirmar_nominas'),
    path("mis-nominas/", views.mis_nominas, name="mis_nominas"), # Empleado

##############################################
##############################################

    path('agregar_sueldo_base/', views.agregar_sueldo_base, name='agregar_sueldo_base'),
    path('calcular_bonificaciones/', views.calcular_bonificaciones, name='calcular_bonificaciones'),
    path('capacitaciones/', views.capacitaciones, name='capacitaciones'),
    
    path('competencias/', views.competencias, name='competencias'),
    path('contratos/', views.contratos, name='contratos'),
    path('costos_de_personal/', views.costos_de_personal, name='costos_de_personal'),
    path('criterios_evaluacion/', views.criterios_evaluacion, name='criterios_evaluacion'),
    path('evaluacion_desempeno/', views.evaluacion_desempeno, name='evaluacion_desempeno'),


    path('instituciones/', views.instituciones, name='instituciones'),
    path('logros/', views.logros, name='logros'),
   
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
