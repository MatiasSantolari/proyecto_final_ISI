from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('home/', views.home, name='home'),
    
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

    ## Habilidad ##
    path('habilidades/', views.habilidades, name='habilidades'),
    path('habilidades/crear/', views.crear_habilidad, name='crear_habilidad'),
    path('habilidades/<int:id_habilidades>/eliminar/', views.eliminar_habilidad, name='eliminar_habilidad'),

    ## SOLICITUDES ##
    path('ofertas/', views.listar_ofertas, name='ofertas_empleo'),
    path('postularse/<int:cargo_id>/', views.postularse_a_cargo, name='postularse'),
    path('postulaciones/', views.ver_postulaciones_admin, name='admin_postulaciones'),
    path('postulaciones/cambiar_estado/', views.cambiar_estado_solicitud, name='cambiar_estado_solicitud'),
    path('postulaciones/finalizar/', views.finalizar_postulaciones_cargo, name='finalizar_postulaciones'),
    path('habilitar_cargo/', views.habilitar_cargo_para_postulaciones, name='habilitar_cargo'),
    path('limpiar_postulantes/', views.limpiar_postulantes_cargo, name='limpiar_postulantes'),


## CATEGORIA del CARGO ##
  #  path('cargo_categoria/', views.cargos_categoria, name='cargo_categoria'),
  #  path('cargo_categoria/crear/', views.crear_cargo_categoria, name='crear_cargo_categoria'), ## Sirve para editar tambien
  #  path('cargo_categoria/<int:id_categoria>/eliminar/', views.eliminar_cargo_categoria, name='eliminar_cargo_categoria'),



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
