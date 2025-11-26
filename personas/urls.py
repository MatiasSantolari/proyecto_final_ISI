from django.urls import path

from personas import views

urlpatterns = [
    path("", views.personas, name="personas"),
    #path("<str:departamento>/<str:tipo_usuario>/", views.personas, name="personas_param"),
    path("crear/", views.crear_persona, name="crear_persona"),
    path("editar/", views.editar_persona, name="editar_persona"),
    path("<int:persona_id>/eliminar/", views.eliminar_persona, name="eliminar_persona"),
    path("cargos_por_departamento/<int:departamento_id>/",views.cargos_por_departamento,name="cargos_por_departamento"),
    path("departamentos_por_tipoUsuario/<int:tipo_usuario>/",views.departamentos_por_tipoUsuario,name="departamentos_por_tipoUsuario"),
    path("perfil/datos-academicos/list/", views.datos_academicos_list, name="datos_academicos_list"),
    path("perfil/datos-academicos/save/", views.datos_academicos_save, name="datos_academicos_save"),
    path("perfil/datos-academicos/delete/", views.datos_academicos_delete, name="datos_academicos_delete"),
    path("perfil/certificaciones/list/", views.certificaciones_list, name="certificaciones_list"),
    path("perfil/certificaciones/save/", views.certificaciones_save, name="certificaciones_save"),
    path("perfil/certificaciones/delete/", views.certificaciones_delete, name="certificaciones_delete"),
    path("perfil/experiencias/list/", views.experiencias_list, name="experiencias_list"),
    path("perfil/experiencias/save/", views.experiencias_save, name="experiencias_save"),
    path("perfil/experiencias/delete/", views.experiencias_delete, name="experiencias_delete"),
]
