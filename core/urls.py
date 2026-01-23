from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import *
from core.views.chatbot import *
from core import api
from core import views 

urlpatterns = [
    path('home/', login_view.home, name='home'),
    path('', login_view.home, name='home'),
    
    path('cambiar_vista/', login_view.cambiar_vista, name='cambiar_vista'),
     
    path('profile/create/', login_view.create_persona, name='create_profile'),
    
    # Perfil usuario
    path('perfil/', login_view.perfil_usuario, name='user_perfil'),
    path('actualizar-cv/', postulaciones_view.actualizar_cv_ajax, name='actualizar_cv_ajax'),


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

    ## INSTITUCION ##
    path('instituciones/', instituciones_view.instituciones, name='instituciones'),
    path('instituciones/crear/', instituciones_view.crear_institucion, name='crear_institucion'),
    path('instituciones/<int:id_institucion>/eliminar/', instituciones_view.eliminar_institucion, name='eliminar_institucion'),
    
    ## LOGRO ##
    path('logros/', logros_view.logros, name='logros'),
    path('logros/crear/', logros_view.crear_logro, name='crear_logro'),
    path('logros/<int:id_logro>/eliminar/', logros_view.eliminar_logro, name='eliminar_logro'),

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
    path('objetivos/desactivar/<int:id_objetivo>/', objetivos_view.desactivar_objetivo, name='desactivar_objetivo'),
    path('objetivos/<int:id_objetivo>/eliminar/', objetivos_view.eliminar_objetivo, name='eliminar_objetivo'),
    path('objetivos/activar/<int:id_objetivo>/', objetivos_view.activar_objetivo, name='activar_objetivo'),
  #  path('objetivos/obtener_datos_asignacion/', objetivos_view.obtener_datos_asignacion, name='obtener_datos_asignacion'),
    path('obtener-datos-depto/', objetivos_view.obtener_datos_por_depto, name='obtener_datos_depto'),
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


    # ASIGNACION DE BENEFICIOS Y DESCUENTOS ##
    path('asignador_beneficio_descuento/', asignar_beneficio_descuento_view.asignador_view, name='asignador_beneficios_descuentos'),
    path('asignador_beneficio_descuento/asignar/', asignar_beneficio_descuento_view.asignar_a_empleados, name='asignar_beneficio_descuento_empleados'),
    path('asignador_beneficio_descuento/ver/<int:empleado_id>/', asignar_beneficio_descuento_view.ver_asignaciones_empleado, name='ver_benef_desc_empleado'),


    ## NOMINAS ##
    path('nominas/', nominas_view.nominas, name='nominas'),
    path('nominas/editar/', nominas_view.editar_nomina, name='editar_nomina'),
    path('nominas/ver/<int:id_nomina>/', nominas_view.ver_nomina, name='ver_nomina'),
    path('nominas/anular/<int:id_nomina>/', nominas_view.anular_nomina, name='anular_nomina'),
    path('nominas/eliminar/<int:id_nomina>/', nominas_view.eliminar_nomina, name='eliminar_nomina'),
    path('nominas/generar/', nominas_view.generar_nominas, name='generar_nominas'),
    path('nominas/confirmar/', nominas_view.confirmar_nominas, name='confirmar_nominas'),
    path("mis-nominas/", nominas_view.mis_nominas, name="mis_nominas"), # Empleado


    ## ASISTENCIA ##
    path('asistencia/registrar/', asistencia_view.registrar_asistencia, name='registrar_asistencia'),
    path('asistencia/confirmar/', asistencia_view.confirmar_asistencias, name='confirmar_asistencias'),
    path('asistencia/confirmar_accion/', asistencia_view.confirmar_asistencias_accion, name='confirmar_asistencias_accion'),


    ## VACACIONES ##
    path("vacaciones/solicitar/", vacaciones_view.solicitar_vacaciones, name="solicitar_vacaciones"),
    path("vacaciones/gestionar/", vacaciones_view.gestionar_vacaciones, name="gestionar_vacaciones"),
    path("vacaciones/cambiar/<int:pk>/<str:accion>/", vacaciones_view.cambiar_estado_vacacion, name="cambiar_estado_vacacion"),
    path("vacaciones/cancelar/<int:pk>/", vacaciones_view.cancelar_vacacion, name="cancelar_vacacion"),


    ## CONTRATOS ##
    path("contratos/", contratos_view.contratos, name="contratos"),
    path("contratos/crear/", contratos_view.crear_contrato, name="crear_contrato"),
    path("contratos/renovar/<int:contrato_id>/", contratos_view.crear_contrato, name="renovar_contrato"),
    path("contratos/finalizar/<int:contrato_id>/", contratos_view.finalizar_contrato, name="finalizar_contrato"),


    path("mis_contratos/", contratos_view.mis_contratos, name="mis_contratos"),

    ## TIPOS DE CONTRATO ##
    path("tipos_contrato/", contratos_view.tipos_contrato, name="tipos_contrato"),
    path("tipos_contrato/crear/", contratos_view.crear_tipo_contrato, name="crear_tipo_contrato"),
    path("tipos_contrato/<int:id_tipo>/eliminar/", contratos_view.eliminar_tipo_contrato, name="eliminar_tipo_contrato"),


    ## INSTITUCION ##
    path('tipos_criterios/', tipo_criterio_view.tiposCriterios, name='tiposCriterios'),
    path('tipos_criterios/crear/', tipo_criterio_view.crear_tipoCriterio, name='crear_tipoCriterio'),
    path('tipos_criterios/<int:id_tipoCriterio>/eliminar/', tipo_criterio_view.eliminar_tipoCriterio, name='eliminar_tipoCriterio'),
    

    ## CRITERIO ##
    path('criterios/', criterios_view.criterios, name='criterios'),
    path('criterios/crear/', criterios_view.crear_criterio, name='crear_criterio'),
    path('criterios/<int:id>/eliminar/', criterios_view.eliminar_criterio, name='eliminar_criterio'),


    ## EVALUACION ##
    path('evaluaciones/', evaluaciones_view.evaluaciones, name='evaluaciones'),
    path('evaluaciones/crear/', evaluaciones_view.crear_evaluacion, name='crear_evaluacion'),
    path('evaluaciones/<int:id_evaluacion>/activar/', evaluaciones_view.activar_evaluacion, name='activar_evaluacion'),
    path('evaluaciones/<int:id_evaluacion>/desactivar/', evaluaciones_view.desactivar_evaluacion, name='desactivar_evaluacion'),
    path('evaluaciones/<int:id_evaluacion>/eliminar/', evaluaciones_view.eliminar_evaluacion, name='eliminar_evaluacion'),
    path('evaluaciones/ver/<int:id_evaluacion>/', evaluaciones_view.ver_evaluacion, name='ver_evaluacion'),
    path('evaluaciones/<int:evaluacion_id>/duplicar/', evaluaciones_view.duplicar_evaluacion, name='duplicar_evaluacion'),

    path("evaluaciones/<int:id_evaluacion>/empleados/", evaluaciones_view.gestionar_empleados, name="evaluacion_empleados"),
    path("evaluaciones/<int:id_evaluacion>/empleados/<int:id_empleado>/asignar/", evaluaciones_view.asignar_empleado, name="asignar_empleado"),
    path("evaluaciones/<int:id_evaluacion>/empleados/<int:id_empleado>/quitar/", evaluaciones_view.quitar_empleado, name="quitar_empleado"),

    path('evaluaciones/<int:id_evaluacion>/empleados/<int:id_empleado>/calificar/', evaluaciones_view.calificar_empleado, name='calificar_empleado'),


    ## CHATBOT ##
    path("chatbot/get_response/", chatbot_view.get_response_chatbot, name="chatbot_response"),


    ###### INFORMES ADM ######
    path('dashboard/', informes_view.dashboard_view, name='dashboard'),
    path('dashboard/api/kpis/', api.api_kpis, name='api_kpis'),
    path('dashboard/api/vacaciones/', api.api_vacaciones, name='api_vacaciones'),
    path('dashboard/api/asistencias/', api.api_asistencias, name='api_asistencias'),
    path('dashboard/api/evaluaciones/', api.api_evaluaciones, name='api_evaluaciones'),
    path('dashboard/api/nominas/', api.api_nominas, name='api_nominas'),
    path('dashboard/api/costo_laboral_comp/', api.api_labor_cost_comparison, name='api_costo_laboral_comp'),
    path('dashboard/api/estructura/', api.api_estructura, name='api_estructura'),
    path('dashboard/api/objetivos/', api.api_objetivos, name='api_objetivos'),

    path('api/departamentos/list/', informes_view.api_departamentos_list, name='api_departamentos_list'),
    
            #### ASISTENCIAS DETALLE ADMIN ####
    path('asistencias/detalle/', informes_view.asistencias_detalle_view, name='asistencias_detalle'),
    path('api/asistencias/detalle/', informes_view.api_asistencias_detalle, name='api_asistencias_detalle'),
    path('api/asistencias/exportar/csv/', informes_view.exportar_asistencias_csv, name='exportar_asistencias_csv'),
    #path('api/asistencias/exportar/pdf/', informes_view.exportar_asistencias_pdf, name='exportar_asistencias_pdf'),
            #### EMPLEADOS DETALLE ADMIN ####
    path('empleados/detalle/', informes_view.empleados_detalle_view, name='empleados_detalle'),
    path('api/empleados/detalle/', informes_view.api_empleados_detalle, name='api_empleados_detalle'),
    path('api/empleados/exportar/csv/', informes_view.exportar_empleados_csv, name='exportar_empleados_csv'),
    path('empleado/<int:empleado_id>/', informes_view.empleado_perfil_detalle_view, name='empleado_perfil_detalle'),
    path('api/empleado/<int:empleado_id>/nominas/', informes_view.api_empleado_nominas, name='api_empleado_nominas'),
    path('api/empleado/<int:empleado_id>/evaluaciones/', informes_view.api_empleado_evaluaciones, name='api_empleado_evaluaciones'),
    path('api/empleado/<int:empleado_id>/asistencia/', informes_view.api_empleado_asistencia, name='api_empleado_asistencia'),
    path('api/empleado/<int:empleado_id>/vacaciones/', informes_view.api_empleado_vacaciones, name='api_empleado_vacaciones'),
    path('api/empleado/<int:empleado_id>/objetivos/', informes_view.api_empleado_objetivos, name='api_empleado_objetivos'),
            #### NOMINAS DETALLE ADMIN ####
    path('nominas/detalle/', informes_view.nominas_detalle_view, name='nominas_detalle'),
    path('api/nominas/detalle/', informes_view.api_nominas_detalle, name='api_nominas_detalle'),
    path('api/nominas/exportar/csv/', informes_view.exportar_nominas_csv, name='exportar_nominas_csv'),
            #### EVALUACIONES DETALLE ADMIN ####
    path('evaluaciones/detalle/', informes_view.evaluaciones_detalle_view, name='evaluaciones_detalle'),
    path('api/evaluaciones/detalle/', informes_view.api_evaluaciones_detalle, name='api_evaluaciones_detalle'),
    path('api/evaluaciones/exportar/csv/', informes_view.exportar_evaluaciones_csv, name='exportar_evaluaciones_csv'),
    path('api/evaluaciones/list/', informes_view.api_evaluaciones_list, name='api_evaluaciones_list'),    

#######################
## INFORMES EMPLEADO ##
    path('dashboard/api/empleado/objetivos/', api.api_dashboard_empleado, name='api_dashboard_empleado'),
    path('dashboard/marcar-objetivo-completado/<int:pk>/', informes_empleado_view.marcar_objetivo_completado, name='marcar_objetivo_completado'),
    path('dashboard/api/empleado/asistencia/', api.api_asistencia_empleado, name='api_asistencia_empleado'),
    path('dashboard/api/empleado/evaluaciones/', api.api_evaluaciones_empleado, name='api_evaluaciones_empleado'),
    path('dashboard/api/empleado/beneficios/', api.api_beneficios_empleado, name='api_beneficios_empleado'),
    path('dashboard/api/empleado/logros/', api.api_logros_empleado, name='api_logros_empleado'),

    path('objetivos/detalle/', informes_view.objetivos_detalle_view, name='objetivos_detalle'),
    path('api/objetivos/detalle/', informes_view.api_objetivos_detalle, name='api_objetivos_detalle'),
    path('asistencias/detalle/', informes_view.asistencias_detalle_view, name='asistencias_detalle'),
    path('api/asistencias/detalle/', informes_view.api_asistencias_detalle, name='api_asistencias_detalle'),
    path('evaluaciones/detalle/', informes_view.evaluaciones_detalle_view, name='evaluaciones_detalle'),
    path('api/evaluaciones/detalle/', informes_view.api_evaluaciones_detalle, name='api_evaluaciones_detalle'),


    path('mi-panel/', informes_empleado_view.dashboard_empleado, name='dashboard_empleado'),
    














##############################################
##############################################

    path('capacitaciones/', views.capacitaciones, name='capacitaciones'),



]
